#!/usr/bin/env python3
"""Write source-bound CHG-35 performance and virtualization evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.performance_contract import CONTRACT_PATH, load_contract  # noqa: E402
from scripts.release_version import assert_candidate_progression, current_release_paths  # noqa: E402

OUTPUT = ROOT / 'evidence/current/release/CHG-35-performance-virtualization.json'
HISTORICAL_ARTIFACTS = (
    'deploy/rc11-release-identity.json',
    'deploy/rc12-release-identity.json',
    'deploy/rc13-release-identity.json',
    'evidence/current/release/rc11-readiness-matrix.json',
    'evidence/current/release/rc11-manifest.json',
    'evidence/current/release/rc11-evidence-binding.json',
    'evidence/current/release/rc12-readiness-matrix.json',
    'evidence/current/release/rc12-manifest.json',
    'evidence/current/release/rc12-evidence-binding.json',
    'evidence/current/release/rc13-readiness-matrix.json',
    'evidence/current/release/rc13-manifest.json',
    'evidence/current/release/rc13-evidence-binding.json',
    'evidence/current/release/CHG-34-ui-accessibility.json',
    'evidence/current/release/CHG-38-release-lifecycle.json',
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(*, verification_path: Path, base_sha: str, contract_path: Path = CONTRACT_PATH, performance_path: Path | None = None) -> dict[str, object]:
    verification = json.loads(verification_path.read_text(encoding='utf-8'))
    if verification.get('code_ready') is not True:
        raise ValueError('CHG-35 evidence requires a passing source verification report.')
    performance_path = performance_path or ROOT / 'evidence/current/performance/qualification.json'
    performance = json.loads(performance_path.read_text(encoding='utf-8'))
    if performance.get('overall_status') != 'PASS':
        raise ValueError('CHG-35 evidence requires a passing aggregate performance qualification.')
    contract, contract_sha256 = load_contract(contract_path)
    if performance.get('contract_sha256') != contract_sha256:
        raise ValueError('Aggregate performance evidence is not bound to the canonical contract.')
    source_commit = verification.get('source_commit')
    source_digest = verification.get('source_digest')
    if performance.get('source_commit') != source_commit or performance.get('source_digest') != source_digest:
        raise ValueError('Aggregate performance evidence is not bound to the verified executable source.')
    progression = assert_candidate_progression(base_sha=base_sha, root=ROOT)
    historical = []
    for relative in HISTORICAL_ARTIFACTS:
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f'Immutable historical artifact is missing: {relative}')
        historical.append({'path': relative, 'sha256': sha256(path), 'immutable': True})
    browser_rows = {row['id']: row for row in performance['workloads'] if row.get('tier_id') == 'browser-ag-grid-scale'}
    synthetic = browser_rows.get('browser-ag-grid-virtualization-5000')
    if not synthetic:
        raise ValueError('Aggregate performance evidence is missing the synthetic virtualization workload.')
    paths = current_release_paths(ROOT)
    return {
        'schema_version': 1,
        'evidence_type': 'change_evidence',
        'change': 'CHG-35',
        'project': 'react-fastapi-base',
        'candidate_version': paths.version.version,
        'artifact_label': paths.version.artifact_label,
        'verified_executable_source': {'commit': source_commit, 'source_digest': source_digest},
        'canonical_contract': {'locator': str(contract_path.relative_to(ROOT)), 'sha256': contract_sha256, 'contract_id': contract['contract_id']},
        'aggregate_performance_evidence': {'locator': str(performance_path.relative_to(ROOT)), 'sha256': sha256(performance_path)},
        'representative_scales': {row['id']: row['scale'] for row in contract['workloads']},
        'structural_virtualization': {
            'workload_id': synthetic['id'],
            'status': synthetic['status'],
            'metrics': synthetic['hard_metrics'],
            'row_recycling_proof': synthetic.get('row_recycling_proof'),
            'selection_result': synthetic.get('selection_result'),
            'sort_result': synthetic.get('sort_result'),
        },
        'api_contract_impact': {'observable_change': False, 'api_major': 1, 'contract_revision': 1, 'base_sha': base_sha.lower()},
        'progression': progression.as_dict(),
        'immutable_historical_artifacts_checked': historical,
        'companyqualification_boundary': {
            'repository_performance_status': 'PASS',
            'company_performance_gate': 'BLOCKED_EXTERNAL',
            'production_ready': False,
            'release_status': 'NOT_CERTIFIED',
            'reason': 'Local/Fabric/CI repository evidence does not constitute authentic company/profile production-like performance evidence.',
        },
        'evidence_policy': 'Repository performance evidence is source-bound regression qualification, not a company performance certification or Project OS GO decision.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, default=ROOT / 'evidence/current/full-stack/verification.json')
    parser.add_argument('--base-sha', required=True)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    evidence = build(verification_path=args.verification.resolve(), base_sha=args.base_sha, contract_path=CONTRACT_PATH)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'evidence': str(output.relative_to(ROOT)), 'status': 'PASS'}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f'CHG-35 evidence FAILED: {error}')
        raise SystemExit(1) from None
