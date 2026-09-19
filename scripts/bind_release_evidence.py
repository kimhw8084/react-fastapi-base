#!/usr/bin/env python3
"""Bind repository evidence to the exact verified source after evidence is committed."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_version import current_release_paths, parse_candidate_version

RELEASE_DIR = ROOT / 'evidence/current/release'
_RELEASE_PATHS = current_release_paths(ROOT)
MANIFEST_PATH = _RELEASE_PATHS.manifest
BINDING_PATH = _RELEASE_PATHS.evidence_binding


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
    parser.add_argument('--target-base-sha')
    args = parser.parse_args()
    verified_source_commit = full_commit(args.verified_source_commit, 'verified source commit')
    evidence_commit = full_commit(args.evidence_commit, 'evidence commit')
    if evidence_commit == verified_source_commit:
        raise ValueError('Evidence commit must remain distinct from verified executable source.')
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    parse_candidate_version(str(manifest.get('version', '')))
    if manifest.get('verified_source_commit') != verified_source_commit:
        raise ValueError('Manifest verified-source binding does not match the requested source commit.')
    target_base_sha = manifest.get('target_base_sha')
    if args.target_base_sha is not None:
        target_base_sha = full_commit(args.target_base_sha, 'target base SHA')
    if target_base_sha is not None and not re.fullmatch(r'[0-9a-fA-F]{40}', target_base_sha):
        raise ValueError('Manifest target base SHA must be a full commit SHA.')
    if target_base_sha == evidence_commit:
        raise ValueError('Evidence commit must remain distinct from the target base SHA.')
    manifest['evidence_commit'] = evidence_commit
    manifest['target_base_sha'] = target_base_sha
    manifest['evidence_binding'] = str(BINDING_PATH.relative_to(ROOT))
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    binding = {
        'schema_version': 2,
        'project': manifest['product'],
        'profile': manifest['profile'],
        'version': manifest['version'],
        'artifact_label': manifest.get('artifact_label', parse_candidate_version(manifest['version']).artifact_label),
        'verified_source_commit': verified_source_commit,
        'source_digest': manifest['source_digest'],
        'evidence_commit': evidence_commit,
        'target_base_sha': target_base_sha,
        'readiness_matrix': {
            'locator': manifest['readiness_matrix']['locator'],
            'sha256': manifest['readiness_matrix']['sha256'],
        },
        'manifest': {
            'locator': str(MANIFEST_PATH.relative_to(ROOT)),
            'sha256': sha256(MANIFEST_PATH),
        },
        'uiqa_matrix': manifest['uiqa_matrix'],
        'performance_qualification': manifest['performance_qualification'],
        'reusable_platform_qualification': manifest['reusable_platform_qualification'],
        'binding_status': 'PASS',
        'result': 'PASS_SOURCE_BOUND_NOT_CERTIFIED',
        'note': 'Source/evidence identity is bound; target_base_sha is the pre-integration base only. Accepted Head and repository merge SHA become available only after their later workflows.',
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
