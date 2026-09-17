#!/usr/bin/env python3
"""Generate the immutable repository-owned RC.11 release identity artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from source_manifest import ROOT, source_digest, source_hashes

IDENTITY_PATH = ROOT / 'deploy/rc11-release-identity.json'
VERSION_PATH = ROOT / 'VERSION'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_commit() -> str:
    result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError('The repository source commit is unavailable.')
    return result.stdout.strip()


def generate(verification_path: Path) -> dict[str, object]:
    try:
        verification = json.loads(verification_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError('The verified release report is missing or invalid.') from error
    if not isinstance(verification, dict) or verification.get('code_ready') is not True:
        raise ValueError('A passing source verification report is required.')

    source_commit = verification.get('source_commit')
    digest = verification.get('source_digest')
    actual_commit = current_commit()
    actual_digest = source_digest()
    if source_commit != actual_commit or digest != actual_digest:
        raise ValueError('The release report is not bound to the current executable source.')

    source_hashes_path = verification_path.parent / str(verification.get('source_hashes', ''))
    if not source_hashes_path.is_file():
        raise ValueError('Verified source-hash evidence is unavailable.')
    try:
        recorded_hashes = json.loads(source_hashes_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError('Verified source-hash evidence is invalid.') from error
    if recorded_hashes != source_hashes():
        raise ValueError('Verified source-hash evidence does not match the current source.')

    version = VERSION_PATH.read_text(encoding='utf-8').strip()
    return {
        'schema_version': 1,
        'identity_type': 'repository_rc11_release',
        'project': 'react-fastapi-base',
        'profile': 'company',
        'candidate_version': version,
        'verified_source_commit': source_commit,
        'source_digest': digest,
        'source_evidence': {
            'locator': str(source_hashes_path.relative_to(ROOT)),
            'sha256': sha256(source_hashes_path),
        },
        'verification': {
            'locator': str(verification_path.relative_to(ROOT)),
            'sha256': sha256(verification_path),
        },
        'generated_by': 'scripts/generate_release_identity.py',
        'code_ready': True,
        'production_ready': False,
        'release_status': 'NOT_CERTIFIED',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, default=ROOT / 'evidence/current/full-stack/verification.json')
    args = parser.parse_args()
    identity = generate(args.verification.resolve())
    encoded = json.dumps(identity, indent=2, sort_keys=True) + '\n'
    if IDENTITY_PATH.exists() and IDENTITY_PATH.read_text(encoding='utf-8') != encoded:
        raise ValueError('The repository release identity already exists with different values.')
    IDENTITY_PATH.write_text(encoded, encoding='utf-8')
    print(json.dumps({'identity': str(IDENTITY_PATH.relative_to(ROOT)), 'status': 'PASS'}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f'Repository release identity FAILED: {error}')
        raise SystemExit(1) from None
