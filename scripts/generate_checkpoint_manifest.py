#!/usr/bin/env python3
"""Generate and verify the deterministic current-source checkpoint manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'CHECKPOINT_MANIFEST.json'
EXCLUDED_PARTS = {
    '.git', '.local', '.evidence', '.pytest_cache', '.venv', '.lab-venv',
    'venv', 'node_modules', 'dist', 'build', 'coverage', 'test-results',
    'playwright-report', 'storybook-static', 'checkpoints', 'evidence',
    '__pycache__', '.cache',
}
EXCLUDED_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.pyc', '.pem', '.key', '.ttf', '.otf', '.woff', '.woff2'}
EXCLUDED_NAMES = {'.coverage', 'coverage.xml'}


def source_files():
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(ROOT)
        if relative.as_posix() == MANIFEST.name or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES or path.name.endswith(('-wal', '-shm', '-journal', '.pid')):
            continue
        if path.name.startswith('.env') and not any(part in path.name for part in ('example', 'sample', 'template')):
            continue
        yield path, relative.as_posix()


def expected_manifest() -> dict[str, object]:
    files = {relative: hashlib.sha256(path.read_bytes()).hexdigest() for path, relative in source_files()}
    return {
        'schema_version': 1,
        'algorithm': 'sha256',
        'self_exclusion': 'CHECKPOINT_MANIFEST.json is excluded from files to avoid recursive hashing.',
        'files': files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = expected_manifest()
    encoded = json.dumps(expected, indent=2, sort_keys=True) + '\n'
    if args.check:
        if not MANIFEST.is_file() or MANIFEST.read_text(encoding='utf-8') != encoded:
            print('Checkpoint manifest is stale; run python scripts/generate_checkpoint_manifest.py.')
            return 1
        print(f'Checkpoint manifest is current: {len(expected["files"])} source files.')
        return 0
    MANIFEST.write_text(encoded, encoding='utf-8')
    print(f'Generated {MANIFEST} with {len(expected["files"])} source files.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
