#!/usr/bin/env python3
"""Write the source-bound CHG-38 change evidence record."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_version import assert_candidate_progression, current_release_paths

OUTPUT = ROOT / 'evidence/current/release/CHG-38-release-lifecycle.json'
HISTORICAL_ARTIFACTS = (
    'deploy/rc11-release-identity.json',
    'deploy/rc12-release-identity.json',
    'evidence/current/release/rc11-readiness-matrix.json',
    'evidence/current/release/rc11-manifest.json',
    'evidence/current/release/rc11-evidence-binding.json',
    'evidence/current/release/rc12-readiness-matrix.json',
    'evidence/current/release/rc12-manifest.json',
    'evidence/current/release/rc12-evidence-binding.json',
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(*, verification_path: Path, base_sha: str) -> dict[str, object]:
    verification = json.loads(verification_path.read_text(encoding='utf-8'))
    if verification.get('code_ready') is not True:
        raise ValueError('CHG-38 evidence requires a passing source verification report.')
    paths = current_release_paths(ROOT)
    source_commit = verification.get('source_commit')
    source_digest = verification.get('source_digest')
    if not isinstance(source_commit, str) or not isinstance(source_digest, str):
        raise ValueError('Source commit and digest are required in the verification report.')
    progression = assert_candidate_progression(base_sha=base_sha, root=ROOT)
    historical = []
    for relative in HISTORICAL_ARTIFACTS:
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f'Immutable historical artifact is missing: {relative}')
        historical.append({'path': relative, 'sha256': sha256(path), 'immutable': True})

    identity_hash = sha256(paths.identity) if paths.identity.is_file() else None
    checkpoint = ROOT / 'CHECKPOINT_MANIFEST.json'
    checkpoint_entry = None
    if checkpoint.is_file():
        checkpoint_document = json.loads(checkpoint.read_text(encoding='utf-8'))
        checkpoint_entry = checkpoint_document.get('files', {}).get(str(paths.identity.relative_to(ROOT)))
    if identity_hash is None or checkpoint_entry != identity_hash:
        raise ValueError('Current release identity must already match CHECKPOINT_MANIFEST before CHG-38 evidence is written.')

    return {
        'schema_version': 1,
        'evidence_type': 'change_evidence',
        'change': 'CHG-38',
        'project': 'react-fastapi-base',
        'candidate_version': paths.version.version,
        'artifact_label': paths.version.artifact_label,
        'derived_artifacts': {
            'identity': str(paths.identity.relative_to(ROOT)),
            'readiness_matrix': str(paths.readiness_matrix.relative_to(ROOT)),
            'manifest': str(paths.manifest.relative_to(ROOT)),
            'evidence_binding': str(paths.evidence_binding.relative_to(ROOT)),
        },
        'verified_source_commit': source_commit,
        'source_digest': source_digest,
        'target_base_sha': base_sha.lower(),
        'progression': progression.as_dict(),
        'immutable_historical_artifacts_checked': historical,
        'api_contract_impact': {
            'observable_change': False,
            'api_major': 1,
            'contract_revision': 1,
            'base_sha': base_sha.lower(),
        },
        'production_boundary': {
            'code_ready': True,
            'production_ready': False,
            'release_status': 'NOT_CERTIFIED',
            'external_blockers': ['identity', 'storage', 'deployment', 'ui_accessibility', 'performance', 'operations'],
        },
        'identity_checkpoint_sha256': identity_hash,
        'checkpoint_entry_sha256': checkpoint_entry,
        'evidence_policy': 'Repository technical release evidence is distinct from external company production qualification; no company PASS evidence is asserted.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, default=ROOT / 'evidence/current/full-stack/verification.json')
    parser.add_argument('--base-sha', required=True)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    evidence = build(verification_path=args.verification.resolve(), base_sha=args.base_sha)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'evidence': str(output.relative_to(ROOT)), 'status': 'PASS'}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f'CHG-38 evidence FAILED: {error}')
        raise SystemExit(1) from None
