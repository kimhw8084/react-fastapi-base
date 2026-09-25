"""CLI for ./dev work-qualify."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from scripts.work_qualification.engine import run
from scripts.work_qualification.reasons import GATES, PHASES
from scripts.work_qualification.safety import UnsafeEvidence, assert_safe, canonical_json, sha256_bytes
from scripts.work_qualification.source import ROOT, repository_identity
from scripts.work_qualification.store import RunStore, compact_status, ensure_private_root


PLAN = [
    {'phase': 0, 'id': 'source_identity', 'automatic': True, 'inputs': ['repository metadata', 'current-version repository release identity', 'deployed build/source binding']},
    {'phase': 1, 'id': 'configuration', 'automatic': True, 'inputs': ['safe BASE_* configuration facts', 'preflight', 'readiness']},
    {'phase': 2, 'id': 'identity', 'automatic': False, 'inputs': ['six real-user browser observations', 'provider per-user isolation and cross-user routing evidence']},
    {'phase': 3, 'id': 'tenant_membership', 'automatic': False, 'inputs': ['dedicated tenant', 'User A admin', 'User B viewer/editor', 'explicit migration acknowledgement']},
    {'phase': 4, 'id': 'storage', 'automatic': False, 'inputs': ['provider SQLite support', 'same-host guarantee', 'disposable doctor check', 'restart/redeploy/backup/restore']},
    {'phase': 5, 'id': 'deployment', 'automatic': False, 'inputs': ['independent frontend/backend', 'HTTPS/runtime API', 'ingress', 'lifecycle/rollback evidence']},
    {'phase': 6, 'id': 'ui_accessibility', 'automatic': False, 'inputs': ['deployed company workflows', 'roles', 'keyboard/accessibility/reflow', 'human assistive-technology evidence']},
    {'phase': 7, 'id': 'performance', 'automatic': True, 'inputs': ['source-bound repository contracts', 'bounded company route observations']},
    {'phase': 8, 'id': 'operations', 'automatic': False, 'inputs': ['existing typed CompanyOperationsEvidence for all seven drills']},
    {'phase': 9, 'id': 'customization', 'automatic': True, 'inputs': ['tracked and untracked paths and hashes']},
    {'phase': 10, 'id': 'final_qualification', 'automatic': True, 'inputs': ['eight existing CompanyQualification gates; no automatic approval']},
]
REFERENCE_PHASES = ('identity', 'tenant_membership', 'storage', 'deployment', 'ui_accessibility', 'performance')


def _root_hint_path() -> Path:
    return Path.home() / '.config' / 'react-fastapi-base' / 'work-qualification-root.json'


def _remember_root(root: Path) -> None:
    path = _root_hint_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != 'nt' and (path.parent.stat().st_mode & 0o077):
            return
        payload = json.dumps({'schema_version': 1, 'evidence_root': str(root)}, sort_keys=True, separators=(',', ':')) + '\n'
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != 'nt': os.chmod(path, 0o600)
    except OSError:
        # The user can still resume by setting the explicit evidence-root variable.
        return


def _remembered_root() -> str:
    try:
        value = json.loads(_root_hint_path().read_text(encoding='utf-8'))
        root = value.get('evidence_root') if isinstance(value, dict) and value.get('schema_version') == 1 else None
        return root if isinstance(root, str) and Path(root).is_absolute() else ''
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return ''


def _root() -> Path:
    value = os.environ.get('BASE_WORK_QUALIFICATION_EVIDENCE_ROOT', '') or _remembered_root()
    if not value:
        if not sys.stdin.isatty():
            raise ValueError('Set BASE_WORK_QUALIFICATION_EVIDENCE_ROOT or run from a terminal to choose a private persistent evidence root.')
        value = input('Private persistent evidence root (absolute path outside this checkout): ').strip()
    try:
        root = ensure_private_root(Path(value), ROOT)
        _remember_root(root)
        return root
    except (OSError, RuntimeError, ValueError):
        raise ValueError('The selected evidence root is not an acceptable private persistent directory.') from None


def _print_plan() -> int:
    version = repository_identity()['candidate_version']
    output = {'schema_version': 1, 'candidate_version': version, 'phases': PLAN, 'gates': list(GATES), 'private_evidence_only': True, 'network_probes_require_explicit_origins': True}
    assert_safe(output)
    print(json.dumps(output, sort_keys=True, separators=(',', ':')))
    return 0


def _latest_state(root: Path) -> tuple[RunStore, dict]:
    store = RunStore.latest(root)
    return store, store.read_state()


def _add_reference(store: RunStore, phase: str, source_path: str) -> None:
    if phase not in REFERENCE_PHASES:
        raise ValueError('Evidence reference phase is not supported.')
    selected = Path(source_path)
    if not selected.is_absolute():
        raise ValueError('Evidence reference source must be an absolute local file.')
    resolved = selected.resolve(strict=True)
    for forbidden in (ROOT.resolve(), store.root.resolve()):
        try:
            resolved.relative_to(forbidden)
        except ValueError:
            continue
        raise ValueError('Evidence reference source must remain outside the checkout and qualification run root.')
    before = resolved.stat()
    if not resolved.is_file() or before.st_size < 1 or before.st_size > 64 * 1024 * 1024:
        raise ValueError('Evidence reference source must be a non-empty local file no larger than 64 MiB.')
    digest = hashlib.sha256()
    with resolved.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    after = resolved.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError('Evidence reference source changed while it was being hashed.')
    reference_dir = store.incoming / 'references' / phase
    reference_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    existing = []
    for item in reference_dir.iterdir():
        match = re.fullmatch(r'evidence-(\d{3,4})\.sha256', item.name)
        if match:
            existing.append(int(match.group(1)))
    number = max(existing, default=0) + 1
    if number > 9999:
        raise ValueError('Qualification evidence reference limit was reached.')
    output = reference_dir / f'evidence-{number:03d}.sha256'
    store.write_reference_digest(output, digest.hexdigest())
    fields = {'phase': phase, 'reference_digest': digest.hexdigest()}
    store.append_event('reference_digest_added', {**fields, 'fingerprint': sha256_bytes(canonical_json(fields))})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Private, resumable work-environment qualification and customization audit.')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--resume', action='store_true', help='Continue the latest durable run in the selected evidence root.')
    modes.add_argument('--status', action='store_true', help='Print a compact summary of the latest run.')
    modes.add_argument('--handoff', action='store_true', help='Print only the <=300-character compact handoff.')
    modes.add_argument('--plan', action='store_true', help='Show the non-mutating qualification plan.')
    modes.add_argument('--reference', nargs=2, metavar=('PHASE', 'FILE'), help='Hash an approved external evidence file into the latest run; never copies the source file or path.')
    args = parser.parse_args(argv)
    try:
        if args.plan:
            return _print_plan()
        root = _root()
        if args.reference:
            store = RunStore.latest(root)
            _add_reference(store, args.reference[0], args.reference[1])
            print(f'Stored only a digest-only evidence reference for {args.reference[0]}; resume to reevaluate.')
            return 0
        if args.status or args.handoff:
            store, state = _latest_state(root)
            if args.status:
                output = compact_status(state)
                assert_safe(output, compact=True)
                print(json.dumps(output, sort_keys=True, separators=(',', ':')))
                return 0
            handoff_path = store.directory / 'handoff.txt'
            handoff = handoff_path.read_text(encoding='utf-8').strip()
            assert_safe({'handoff': handoff}, compact=True)
            if len(handoff) > 300:
                raise ValueError('Stored compact handoff is invalid.')
            print(handoff)
            return 0
        if args.resume:
            store = RunStore.latest(root)
        else:
            store = RunStore.create(root, source=repository_identity())
        handoff = run(store)
        state = store.read_state()
        summary = compact_status(state)
        assert_safe(summary, compact=True)
        print(json.dumps(summary, sort_keys=True, separators=(',', ':')))
        print(handoff)
        print(f"Private run input folder: runs/{store.run_id}/incoming")
        print('The private detailed report is report.md; rerun with --resume after adding safe observations.')
        return 0
    except Exception:
        # Avoid exception text: path and validation errors can include operator-supplied data.
        print('Work-environment qualification could not safely continue. Review the selected private run locally.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
