#!/usr/bin/env python3
"""Bind RC.11 evidence to the exact verified source after evidence is committed."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / 'evidence/current/release'
MANIFEST_PATH = RELEASE_DIR / 'rc11-manifest.json'
BINDING_PATH = RELEASE_DIR / 'rc11-evidence-binding.json'


def full_commit(value: str, label: str) -> str:
    if not re.fullmatch(r'[0-9a-fA-F]{40}', value):
        raise ValueError(f'{label} must be a full commit SHA.')
    return value.lower()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verified-source-commit', required=True)
    parser.add_argument('--evidence-commit', required=True)
    parser.add_argument('--accepted-head', required=True)
    parser.add_argument('--repository-merge-sha', required=True)
    args = parser.parse_args()
    verified_source_commit = full_commit(args.verified_source_commit, 'verified source commit')
    evidence_commit = full_commit(args.evidence_commit, 'evidence commit')
    accepted_head = full_commit(args.accepted_head, 'Accepted Head')
    repository_merge_sha = full_commit(args.repository_merge_sha, 'repository merge SHA')
    if evidence_commit == verified_source_commit:
        raise ValueError('Evidence commit must remain distinct from verified executable source.')
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    if manifest.get('verified_source_commit') != verified_source_commit:
        raise ValueError('Manifest verified-source binding does not match the requested source commit.')
    manifest['evidence_commit'] = evidence_commit
    manifest['accepted_head'] = accepted_head
    manifest['repository_merge_sha'] = repository_merge_sha
    manifest['evidence_binding'] = str(BINDING_PATH.relative_to(ROOT))
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    binding = {
        'schema_version': 2,
        'project': manifest['product'],
        'profile': manifest['profile'],
        'version': manifest['version'],
        'verified_source_commit': verified_source_commit,
        'source_digest': manifest['source_digest'],
        'evidence_commit': evidence_commit,
        'accepted_head': accepted_head,
        'repository_merge_sha': repository_merge_sha,
        'readiness_matrix': {
            'locator': manifest['readiness_matrix']['locator'],
            'sha256': manifest['readiness_matrix']['sha256'],
        },
        'manifest': {
            'locator': str(MANIFEST_PATH.relative_to(ROOT)),
            'sha256': sha256(MANIFEST_PATH),
        },
        'binding_status': 'PASS',
        'result': 'PASS_SOURCE_BOUND_NOT_CERTIFIED',
        'note': 'Source/evidence identity is bound; company gates and production approval remain independent.',
    }
    BINDING_PATH.write_text(json.dumps(binding, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'binding': str(BINDING_PATH.relative_to(ROOT)), 'status': binding['binding_status']}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f'Release evidence binding FAILED: {error}')
        raise SystemExit(1) from None
