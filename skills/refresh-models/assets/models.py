#!/usr/bin/env python3
"""Offline role assignments and explicit, atomic refresh of project recommendations."""
import argparse
from datetime import date
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('harness_profile', ROOT / 'skills/config/assets/profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)
SLOTS = ('executor', 'readonly', 'advisor')
DOMAINS = {'developers.openai.com', 'platform.openai.com', 'learn.chatgpt.com'}


def decode(raw):
    return json.loads(raw, object_pairs_hook=profile.json_object)


def defaults():
    text = (ROOT / 'skills/start-workflow/references/agent-topology.md').read_text()
    body = text.split('<!-- topology:defaults-begin -->')[1].split('<!-- topology:defaults-end -->')[0]
    rows = re.findall(r'^\| `([a-z]+)` \| [^|]+ \| `([^`]+)` \| `([^`]+)` \|$', body, re.M)
    result = {slot: dict(model=model, effort=effort) for slot, model, effort in rows}
    if set(result) != set(profile.SLOTS) or len(rows) != 4 or result['orchestrator'] != dict(model='session', effort='inherit'):
        raise ValueError('INVALID_DEFAULTS')
    for slot in SLOTS:
        profile.validate_slot(slot, result[slot])
    return result


def concrete_efforts(slot, effort):
    if effort != 'tiered':
        return {effort}
    return {'high', 'max'} if slot == 'executor' else {'xhigh', 'max'}


def validate(data):
    keys = {'schema_version', 'checked_at', 'sources', 'models', 'rationale', 'host_models'}
    if not isinstance(data, dict) or set(data) != keys or type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('INVALID_MODELS: schema')
    checked = data['checked_at']
    if not isinstance(checked, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', checked) or date.fromisoformat(checked) > date.today():
        raise ValueError('INVALID_MODELS: checked_at')
    sources = data['sources']
    if not isinstance(sources, list) or not sources:
        raise ValueError('INVALID_MODELS: sources')
    for source in sources:
        url = urlsplit(source) if isinstance(source, str) else None
        if url is None or url.scheme != 'https' or url.hostname not in DOMAINS or url.username or url.password:
            raise ValueError('INVALID_MODELS: official source required')
    if not isinstance(data['models'], dict) or set(data['models']) != set(SLOTS):
        raise ValueError('INVALID_MODELS: three managed slots required')
    if not isinstance(data['rationale'], dict) or set(data['rationale']) != set(SLOTS) or not all(isinstance(v, str) and v.strip() for v in data['rationale'].values()):
        raise ValueError('INVALID_MODELS: rationale required per slot')
    host = data['host_models']
    if not isinstance(host, dict):
        raise ValueError('INVALID_MODELS: host_models')
    for model, efforts in host.items():
        profile.validate_slot('readonly', {'model': model})
        if not isinstance(efforts, list) or not efforts or any(not isinstance(e, str) or e not in profile.EFFORTS or e == 'tiered' for e in efforts):
            raise ValueError('INVALID_MODELS: host efforts')
    for slot, record in data['models'].items():
        profile.validate_slot(slot, record)
        if 'effort' not in record or not concrete_efforts(slot, record['effort']) <= set(host.get(record['model'], [])):
            raise ValueError('INVALID_MODELS: unsupported model/effort: ' + slot)
    return data


def read(path):
    if path.is_symlink():
        raise ValueError('INVALID_MODELS: symlink')
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None, None
    try:
        return raw, validate(decode(raw))
    except (ValueError, TypeError) as exc:
        raise ValueError("INVALID_MODELS: " + str(exc)) from exc


def digest(raw):
    return hashlib.sha256(raw).hexdigest() if raw is not None else 'missing'


def compact_flags(text):
    result = {}
    for item in text.split(','):
        slot, sep, value = item.strip().partition('=')
        if not sep or slot not in profile.SLOTS or slot in result:
            raise ValueError('INVALID_FLAGS: slot')
        if value == 'default':
            result[slot] = None
            continue
        model, sep, effort = value.rpartition('@')
        record = dict(model=model, effort=effort) if sep else dict(model=value)
        try:
            profile.validate_slot(slot, record)
        except profile.ProfileError as exc:
            raise ValueError("INVALID_FLAGS: " + str(exc)) from exc
        result[slot] = record
    return result


def resolve(base, managed, overrides, flags=None):
    """Replace complete records; model-only overrides retain bundled effort policy."""
    recommended = {**base, **(managed['models'] if managed else {})}
    models, sources, diagnostics = dict(recommended), {s: 'managed' if managed and s in SLOTS else 'bundled' for s in base}, []
    for slot, record in overrides.items():
        try:
            profile.validate_slot(slot, record)
        except profile.ProfileError as exc:
            diagnostics.append(str(exc) + '; use saved recommendation or bundled default')
            continue
        models[slot] = {'effort': base[slot]['effort'], **record}
        sources[slot] = 'profile'
    for slot, record in (flags or {}).items():
        models[slot] = dict(recommended[slot]) if record is None else {'effort': base[slot]['effort'], **record}
        sources[slot] = 'default' if record is None else 'flag'
    if 'orchestrator' in overrides or 'orchestrator' in (flags or {}):
        diagnostics.append('SESSION_ORCHESTRATOR: override ignored; current session retained')
    models['orchestrator'] = dict(base['orchestrator'])
    sources['orchestrator'] = 'session'
    return dict(models=models, sources=sources, diagnostics=diagnostics)


def apply(path, raw, rendered, expected):
    if digest(raw) != expected:
        raise ValueError('STALE_MODELS: expected hash differs')
    if raw is not None:
        return profile.apply(path, raw, rendered, expected)
    # Publish first creation without replacing a concurrent creator's file.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.models-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ValueError('STALE_MODELS: created since preview') from exc
        return True
    finally:
        os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('resolve', 'edit'))
    parser.add_argument('--cwd', required=True)
    parser.add_argument('--topology-models')
    parser.add_argument('--candidate', default='-', help='Complete recommendation JSON; - reads stdin')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    try:
        resolved = profile.resolve(args.cwd, 'be')
        path = Path(resolved['profile_path']).parent / 'be-harness/models.json'
        raw, managed = read(path)
        base = defaults()
        before = resolve(base, managed, resolved['values'].get('topologyModels', {}))
        before['diagnostics'] = resolved['diagnostics'] + before['diagnostics']
        if args.action == 'resolve':
            if args.apply or args.expected_sha256 or args.candidate != '-':
                raise ValueError('INVALID_ARGUMENT: edit-only option')
            result = resolve(base, managed, resolved['values'].get('topologyModels', {}), compact_flags(args.topology_models) if args.topology_models is not None else None)
            result['diagnostics'] = resolved['diagnostics'] + result['diagnostics']
            result.update(status='DONE', sha256=digest(raw), recommendation=managed)
        else:
            if args.topology_models is not None:
                raise ValueError('INVALID_ARGUMENT: resolve-only option')
            candidate = validate(decode(sys.stdin.read() if args.candidate == '-' else Path(args.candidate).read_text()))
            rendered = json.dumps(candidate, ensure_ascii=False, indent=2).encode() + b'\n'
            if managed == candidate:
                rendered = raw
            changed = apply(path, raw, rendered, args.expected_sha256) if args.apply else raw != rendered
            result = dict(status='DONE' if args.apply else 'PREVIEW', changed=changed,
                          sha256_before=digest(raw), sha256_after=digest(rendered), preview=candidate,
                          before=before, after=resolve(base, candidate, resolved['values'].get('topologyModels', {})))
        result.update(models_path=str(path), profile_path=resolved['profile_path'], inherited=resolved['inherited'])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        print(json.dumps(dict(status='BLOCKED', error=str(exc).replace('STALE_PROFILE', 'STALE_MODELS')), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
