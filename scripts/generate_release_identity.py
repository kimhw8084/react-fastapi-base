#!/usr/bin/env python3
"""Generate the immutable repository-owned current release identity artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_version import current_release_paths, parse_candidate_version
from scripts.source_manifest import executable_source_commit, source_digest, source_hashes

# Kept as an import-compatible view for tooling/tests; main() resolves it again
# from the current VERSION immediately before writing.
IDENTITY_PATH = current_release_paths(ROOT).identity
VERSION_PATH = ROOT / 'VERSION'


def generate(verification_path: Path, *, stable_promotion: bool = False) -> dict[str, object]:
    try:
        verification = json.loads(verification_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError('The verified release report is missing or invalid.') from error
    if not isinstance(verification, dict) or verification.get('code_ready') is not True:
        raise ValueError('A passing source verification report is required.')

    source_commit = verification.get('source_commit')
    digest = verification.get('source_digest')
    actual_commit = executable_source_commit(ROOT)
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

    version = parse_candidate_version(VERSION_PATH.read_text(encoding='utf-8').strip())
    if version.is_stable and not stable_promotion:
        raise ValueError('Stable release identity generation requires explicit stable promotion mode.')
    recorded_version = verification.get('candidate_version')
    if recorded_version is not None and recorded_version != version.version:
        raise ValueError('The release report candidate version does not match VERSION.')
    return {
        'schema_version': 1,
        'identity_type': 'repository_release',
        'project': 'react-fastapi-base',
        'profile': 'company',
        'candidate_version': version.version,
        'verified_source_commit': source_commit,
        'source_digest': digest,
        'source_evidence': {
            'locator': str(source_hashes_path.relative_to(ROOT)),
            'sha256': hashlib.sha256(source_hashes_path.read_bytes()).hexdigest(),
        },
        'generated_by': 'scripts/generate_release_identity.py',
        'code_ready': True,
        'production_ready': False,
        'release_status': 'NOT_CERTIFIED',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, default=ROOT / 'evidence/current/full-stack/verification.json')
    parser.add_argument('--replace', action='store_true', help='Allow the canonical finalization path to rebind an existing identity.')
    parser.add_argument('--stable-promotion', action='store_true', help='Explicitly allow a stable VERSION identity.')
    args = parser.parse_args()
    identity = generate(args.verification.resolve(), stable_promotion=args.stable_promotion)
    encoded = json.dumps(identity, indent=2, sort_keys=True) + '\n'
    identity_path = current_release_paths(ROOT).identity
    if identity_path.exists() and identity_path.read_text(encoding='utf-8') != encoded and not args.replace:
        raise ValueError('The repository release identity already exists with different values.')
    identity_path.write_text(encoded, encoding='utf-8')
    print(json.dumps({'identity': str(identity_path.relative_to(ROOT)), 'status': 'PASS'}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f'Repository release identity FAILED: {error}')
        raise SystemExit(1) from None
