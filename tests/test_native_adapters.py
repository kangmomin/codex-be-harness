"""Behavioral coverage for the native profile and entry adapters."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

profile = load('native_profile', 'skills/config/assets/profile.py')
policy = load('native_policy', 'skills/start-workflow/assets/workflow_policy.py')
doctor = load('native_doctor', 'skills/config/assets/doctor.py')

class NativeProfileTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codex profile ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_profile(self, text):
        path = self.root / '.codex/be-harness.local.md'
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(text)
        return path

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True, text=True).stdout.strip()

    def test_native_schema_and_slot_boundaries(self):
        schema = profile.schema('be')
        self.assertIn('topologyModels', schema)
        self.assertIn('feedbackUpstreamRepo', schema)
        self.assertNotIn('codexModels', schema)
        self.assertNotIn('codexMode', schema)
        profile.validate_slot('executor', {'model': 'example-model', 'effort': 'tiered'})
        profile.validate_slot('advisor', {'model': 'example-model', 'effort': 'tiered'})
        for slot, value in [('review', {'model': 'model'}), ('readonly', {'model': 'model', 'effort': 'tiered'}), ('orchestrator', {'model': 'model', 'effort': 'tiered'}), ('executor', {'model': 'vendor/model'}), ('executor', {'provider': 'openai', 'model': 'model'})]:
            with self.subTest(slot=slot, value=value), self.assertRaises(profile.ProfileError):
                profile.validate_slot(slot, value)

    def test_missing_profile_cannot_fall_back_to_detected_go(self):
        (self.root / 'go.mod').write_text('module example\n')
        with self.assertRaisesRegex(profile.ProfileError, 'NO_PROFILE'):
            profile.resolve(self.root, 'be')

    def test_native_profile_preserves_empty_and_does_not_infer_preset(self):
        self.write_profile(b'---\ntestCommand: ""\n---\nnotes\n')
        (self.root / 'go.mod').write_text('module example\n')
        result = profile.resolve(self.root, 'be')
        self.assertEqual('', result['commands']['testCommand']['value'])
        self.assertNotIn('preset', result['values'])
        self.assertEqual('.codex/harness-reports', result['values']['reportDir'])
        self.assertEqual(['AGENTS.md'], result['values']['projectConventions'])

    def test_edit_preserves_body_comments_crlf_and_rejects_stale_write(self):
        original = b'---\r\nlanguage: ko # keep\r\nsourceDirs: ["src/"]\r\n---\r\n# Notes\r\nkeep bytes\r\n'
        path = self.write_profile(original)
        changes = {'language': 'en', 'sourceDirs': ['src/', 'path,comma/']}
        rendered = profile.Document(original).edit(changes, 'be')
        self.assertTrue(rendered.endswith(b'---\r\n# Notes\r\nkeep bytes\r\n'))
        self.assertIn(b'# keep\r\n', rendered)
        digest = hashlib.sha256(original).hexdigest()
        self.assertTrue(profile.apply(path, original, rendered, digest))
        with self.assertRaisesRegex(profile.ProfileError, 'STALE_PROFILE'):
            profile.apply(path, original, rendered, digest)
        self.assertEqual(rendered, path.read_bytes())

    def test_slot_patch_does_not_merge_record_fields_or_leave_invalid_slot(self):
        original = b'---\ntopologyModels:\n  executor: { model: example-model, effort: high }\n  advisor: { model: advisor-model }\n---\n'
        changed = profile.Document(original).edit({'topologyModels': {'executor': {'model': 'next-model'}}}, 'be')
        values = profile.Document(changed).value('topologyModels', 'be')
        self.assertEqual({'model': 'next-model'}, values['executor'])
        self.assertEqual({'model': 'advisor-model'}, values['advisor'])
        invalid = original.replace(b'advisor:', b'unknown:')
        with self.assertRaises(profile.ProfileError):
            profile.Document(invalid).edit({'topologyModels': {'executor': {'model': 'next-model'}}}, 'be')

    def test_worktree_resolve_and_cli_apply_use_inherited_file(self):
        self.git('init', '-q'); self.git('config', 'user.name', 'Fixture'); self.git('config', 'user.email', 'fixture@example.invalid')
        (self.root / 'tracked').write_text('base\n'); self.git('add', 'tracked'); self.git('commit', '-qm', 'base')
        path = self.write_profile(b'---\npreset: custom\nlanguage: ko\n---\n# Notes\n')
        worker = self.root / 'worker'
        self.git('worktree', 'add', '-qb', 'worker', str(worker))
        result = profile.resolve(worker, 'be')
        self.assertEqual(str(path), result['profile_path']); self.assertTrue(result['inherited'])
        script = ROOT / 'skills/config/assets/profile.py'
        args = [sys.executable, '-B', str(script), 'edit', '--domain', 'be', '--cwd', str(worker)]
        preview = subprocess.run(args, input='{"language":"en"}', text=True, capture_output=True, check=True)
        digest = json.loads(preview.stdout)['sha256_before']
        applied = subprocess.run(args + ['--apply', '--expected-sha256', digest], input='{"language":"en"}', text=True, capture_output=True, check=True)
        self.assertEqual(str(path), json.loads(applied.stdout)['profile_path'])
        self.assertIn(b'language: en', path.read_bytes())
        self.assertFalse((worker / '.codex').exists())

    def test_empty_slot_object_resets_and_invalid_slot_can_be_repaired(self):
        original = b'---\ntopologyModels:\n  executor: { model: example-model, effort: invalid }\n---\n'
        doc = profile.Document(original)
        reset = doc.edit({'topologyModels': {}}, 'be')
        self.assertEqual({}, profile.Document(reset).value('topologyModels', 'be'))
        deleted = doc.edit({'topologyModels': {'executor': None}}, 'be')
        self.assertEqual({}, profile.Document(deleted).value('topologyModels', 'be'))
        repaired = doc.edit({'topologyModels': {'executor': {'model': 'example-model', 'effort': 'high'}}}, 'be')
        self.assertEqual('high', profile.Document(repaired).value('topologyModels', 'be')['executor']['effort'])
        populated = profile.Document(reset).edit({'topologyModels': {'advisor': {'model': 'advisor-model'}}}, 'be')
        self.assertEqual({'advisor': {'model': 'advisor-model'}}, profile.Document(populated).value('topologyModels', 'be'))

    def test_reset_cannot_remove_slot_comment(self):
        original = b'---\ntopologyModels:\n  executor: { model: example-model } # keep\n---\n'
        with self.assertRaisesRegex(profile.ProfileError, 'UNSUPPORTED_LAYOUT'):
            profile.Document(original).edit({'topologyModels': {}}, 'be')

    def test_doctor_is_offline_and_invalid_topology_is_warning(self):
        self.write_profile(b'---\npreset: custom\ntopologyModels:\n  readonly: { model: model, effort: tiered }\n---\n')
        result = doctor.diagnose(self.root, 'be', 'codex')
        self.assertEqual('none', result['downloads'])
        self.assertFalse(result['validation_executed'])
        self.assertEqual('CHECKS_INCOMPLETE', result['status'])
        self.assertTrue(any(x['status'] == 'INVALID_SLOT' for x in result['checks']))

class NativeEntryTest(unittest.TestCase):
    def route(self, args, **extra):
        return policy.route(dict(entry='be', arguments=args, installed={}, **extra))

    def test_native_modes_and_publish_scope(self):
        self.assertEqual('pr', self.route([])['publish_policy'])
        self.assertEqual('push', self.route(['--hard'])['publish_policy'])
        self.assertEqual('local', self.route([], inherited_publish_policy='local')['publish_policy'])
        self.assertEqual('none', self.route(['--verify'])['publish_policy'])
        self.assertEqual('BLOCKED:MODE_CONFLICT', self.route(['--verify', '--analyze'])['status'])

    def test_unsupported_domain_provider_and_flag_values(self):
        for option in ('--fs', '--mm', '--codex'):
            args = [option, 'max'] if option == '--codex' else [option]
            self.assertTrue(self.route(args)['status'].startswith('BLOCKED:'))
        self.assertEqual('build', self.route(['--topology-models', '--verify'])['mode'])
        self.assertEqual('build', self.route(['--', '--verify'])['mode'])
        with self.assertRaises(ValueError):
            self.route(['--topology-models'])

    def test_resume_preserves_local_and_rejects_mode_collision(self):
        saved = dict(resume_mode='be', resume_hard=True, resume_publish_policy='local', resume_route_target='be')
        self.assertEqual('local', self.route(['--resume', '/tmp/state'], **saved)['publish_policy'])
        self.assertEqual('BLOCKED:RUN_MISMATCH', self.route(['--resume', '/tmp/state', '--verify'], **saved)['status'])

if __name__ == '__main__':
    unittest.main()
