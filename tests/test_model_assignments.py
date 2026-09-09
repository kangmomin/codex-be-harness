"""Recommendations stay offline, preserve overrides, and publish only verified candidates."""
from datetime import date
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/refresh-models/assets/models.py'
spec = importlib.util.spec_from_file_location('model_assignments', SCRIPT)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)


def candidate():
    return dict(schema_version=1, checked_at=date.today().isoformat(),
                sources=['https://developers.openai.com/api/docs/guides/latest-model'],
                models={s: dict(model='supported-model', effort='tiered' if s == 'advisor' else 'high') for s in models.SLOTS},
                rationale={s: 'Official guide and host capability evidence' for s in models.SLOTS},
                host_models={'supported-model': ['high', 'xhigh', 'max']})


class ModelAssignmentsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='harness models ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / '.codex/be-harness.local.md'
        self.profile.parent.mkdir()
        self.profile.write_text('---\npreset: custom\ntopologyModels:\n  executor: { model: user-model, effort: high }\n---\n# Preserve notes\n')
        self.path = self.profile.parent / 'be-harness/models.json'

    def cli(self, *args, data=None, expected=0, cwd=None):
        result = subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), *args, '--cwd', str(cwd or self.root)],
                                input=json.dumps(data) if data is not None else None,
                                capture_output=True, text=True)
        self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout if result.returncode == 0 else result.stderr)

    def test_offline_default_and_profile_resolution_does_not_create_files(self):
        result = self.cli('resolve')
        self.assertEqual(dict(model='session', effort='inherit'), result['models']['orchestrator'])
        self.assertEqual('user-model', result['models']['executor']['model'])
        self.assertEqual(models.defaults()['advisor'], result['models']['advisor'])
        self.assertEqual('missing', result['sha256'])
        self.assertFalse(self.path.exists())

    def test_preview_apply_preserves_profile_and_user_overrides(self):
        original = self.profile.read_bytes()
        new = candidate()
        preview = self.cli('edit', data=new)
        self.assertFalse(self.path.exists())
        self.assertEqual('user-model', preview['after']['models']['executor']['model'])
        self.assertEqual('supported-model', preview['after']['models']['advisor']['model'])
        applied = self.cli('edit', '--apply', '--expected-sha256', preview['sha256_before'], data=new)
        self.assertEqual('DONE', applied['status'])
        self.assertEqual(new, json.loads(self.path.read_text()))
        self.assertEqual(original, self.profile.read_bytes())
        self.assertEqual('managed', self.cli('resolve')['sources']['advisor'])
        before = self.path.stat().st_mtime_ns
        again = self.cli('edit', '--apply', '--expected-sha256', applied['sha256_after'], data=new)
        self.assertFalse(again['changed'])
        self.assertEqual(before, self.path.stat().st_mtime_ns)

    def test_precedence_default_and_model_only_effort(self):
        new = candidate()
        new['models']['advisor']['effort'] = 'high'
        base = models.defaults()
        result = models.resolve(base, new, {'advisor': {'model': 'user-advisor'}, 'executor': {'model': 'user-worker'}},
                                models.compact_flags('executor=default'))
        self.assertEqual('supported-model', result['models']['executor']['model'])
        self.assertEqual(dict(model='user-advisor', effort='tiered'), result['models']['advisor'])
        result = models.resolve(base, new, {'executor': {'model': 'user-worker'}}, models.compact_flags('executor=flag-worker'))
        self.assertEqual(dict(model='flag-worker', effort='high'), result['models']['executor'])
        self.assertEqual('supported-model', models.resolve(base, new, {})['models']['executor']['model'])
        invalid = models.resolve(base, new, {'readonly': {'model': 'bad', 'effort': 'tiered'}})
        self.assertEqual(new['models']['readonly'], invalid['models']['readonly'])
        self.assertTrue(invalid['diagnostics'])

    def test_legacy_orchestrator_is_warned_and_never_replaces_session(self):
        for flags in ('orchestrator=other-model@high', 'orchestrator=default'):
            result = models.resolve(models.defaults(), None, {'orchestrator': {'model': 'legacy-model'}}, models.compact_flags(flags))
            self.assertEqual(dict(model='session', effort='inherit'), result['models']['orchestrator'])
            self.assertTrue(any('SESSION_ORCHESTRATOR' in d for d in result['diagnostics']))

    def test_invalid_profile_slot_uses_managed_recommendation_with_warning(self):
        self.cli('edit', '--apply', '--expected-sha256', 'missing', data=candidate())
        self.profile.write_text('---\npreset: custom\ntopologyModels:\n  readonly: { model: wrong-model, effort: tiered }\n---\n')
        result = self.cli('resolve')
        self.assertEqual('supported-model', result['models']['readonly']['model'])
        self.assertTrue(any('INVALID_SLOT' in d for d in result['diagnostics']))

    def test_invalid_flags_are_rejected_as_whole_batch(self):
        for flags in ('executor=ok,readonly=bad@tiered', 'executor=ok,executor=duplicate', 'executor=ok,', 'worker=unknown', ''):
            with self.subTest(flags=flags):
                self.cli('resolve', '--topology-models', flags, expected=2)
        self.assertFalse(self.path.exists())

    def test_missing_evidence_and_unsupported_effort_do_not_write(self):
        for field, value in [('sources', []), ('sources', ['https://example.com/models']),
                             ('host_models', {'supported-model': ['high']}), ('checked_at', '2999-01-01'),
                             ('schema_version', True), ('rationale', {})]:
            data = candidate()
            data[field] = value
            with self.subTest(field=field):
                self.cli('edit', '--apply', '--expected-sha256', 'missing', data=data, expected=2)
                self.assertFalse(self.path.exists())
        data = candidate()
        data['models']['orchestrator'] = dict(model='supported-model', effort='high')
        self.cli('edit', data=data, expected=2)

    def test_stale_create_and_update_preserve_existing_bytes(self):
        old = candidate()
        preview = self.cli('edit', data=old)
        self.cli('edit', '--apply', '--expected-sha256', 'missing', data=old)
        original = self.path.read_bytes()
        newer = candidate()
        newer['rationale']['advisor'] = 'Changed evidence'
        stale = self.cli('edit', '--apply', '--expected-sha256', preview['sha256_before'], data=newer, expected=2)
        self.assertIn('STALE_MODELS', stale['error'])
        self.assertEqual(original, self.path.read_bytes())
        preview = self.cli('edit', data=newer)
        concurrent = original + b'\n'
        self.path.write_bytes(concurrent)
        self.cli('edit', '--apply', '--expected-sha256', preview['sha256_before'], data=newer, expected=2)
        self.assertEqual(concurrent, self.path.read_bytes())

    def test_corrupt_duplicate_and_symlink_files_are_preserved(self):
        self.path.parent.mkdir()
        for raw in (b'{broken', b'{"schema_version":1,"schema_version":1}'):
            self.path.write_bytes(raw)
            self.cli('resolve', expected=2)
            self.cli('edit', data=candidate(), expected=2)
            self.assertEqual(raw, self.path.read_bytes())
        self.path.unlink()
        self.path.symlink_to(self.profile)
        original = self.profile.read_bytes()
        self.cli('edit', data=candidate(), expected=2)
        self.assertEqual(original, self.profile.read_bytes())

    def test_linked_worktree_refresh_shares_profile_recommendation_location(self):
        def git(*args):
            subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)
        git('init', '-q')
        git('config', 'user.name', 'Fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        (self.root / 'tracked').write_text('base\n')
        git('add', 'tracked')
        git('commit', '-qm', 'base')
        worker = self.root / 'worktree'
        git('worktree', 'add', '-qb', 'worker', str(worker))
        result = self.cli('edit', '--apply', '--expected-sha256', 'missing', data=candidate(), cwd=worker)
        self.assertTrue(result['inherited'])
        self.assertEqual(str(self.path), result['models_path'])
        self.assertFalse((worker / '.codex').exists())


if __name__ == '__main__':
    unittest.main()
