#!/usr/bin/env python3
"""Validate and write the source-bound aggregate performance qualification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.performance_contract import (
    CONTRACT_PATH,
    PerformanceContractError,
    load_contract,
    reconcile_reports,
    sha256_file,
    validate_contract,
)
from scripts.source_manifest import executable_source_commit, source_digest, source_hashes
DEFAULT_OUTPUT = ROOT / 'evidence/current/performance/qualification.json'
REPORT_PATHS = {
    'owned-pure-algorithms': ROOT / 'evidence/current/performance/owned-algorithms.json',
    'platform-data-volume': ROOT / 'evidence/current/performance/stress.json',
    'browser-ag-grid-scale': ROOT / 'evidence/current/performance/browser.json',
}


def _read_report(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise PerformanceContractError(f'Cannot read performance report {path}: {error}') from error
    if not isinstance(value, dict):
        raise PerformanceContractError(f'Performance report {path} must contain an object.')
    return value


def validate_contract_only(contract_path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract, digest = load_contract(contract_path)
    return {'contract_id': contract['contract_id'], 'contract_sha256': digest, 'workloads': len(contract['workloads']), 'status': 'PASS'}


def build_qualification(
    *,
    contract_path: Path = CONTRACT_PATH,
    report_paths: dict[str, Path] | None = None,
    output: Path = DEFAULT_OUTPUT,
    expected_source_commit: str | None = None,
    expected_source_digest: str | None = None,
    candidate_version: str | None = None,
) -> dict[str, Any]:
    contract, contract_sha256 = load_contract(contract_path)
    report_paths = report_paths or REPORT_PATHS
    reports: dict[str, dict[str, Any]] = {}
    report_locators: dict[str, str] = {}
    report_hashes: dict[str, str] = {}
    for tier_id, path in report_paths.items():
        reports[tier_id] = _read_report(path)
        report_locators[tier_id] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        report_hashes[tier_id] = sha256_file(path)
    source_hash_map = source_hashes()
    source_commit = expected_source_commit or executable_source_commit(ROOT)
    digest = expected_source_digest or source_digest(source_hash_map)
    qualification = reconcile_reports(
        contract,
        reports,
        expected_source_commit=source_commit,
        expected_source_digest=digest,
        expected_contract_sha256=contract_sha256,
        report_locators=report_locators,
        report_hashes=report_hashes,
        candidate_version=candidate_version,
    )
    qualification['contract'] = {'locator': str(contract_path.relative_to(ROOT)), 'sha256': contract_sha256}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(qualification, indent=2) + '\n', encoding='utf-8')
    return qualification


def write_failure(output: Path, error: Exception, *, contract_path: Path = CONTRACT_PATH) -> None:
    try:
        contract, contract_sha256 = load_contract(contract_path)
        workloads = [
            {
                'id': workload['id'],
                'tier_id': workload['tier_id'],
                'scale': workload['scale'],
                'budgets': workload['budgets'],
                'status': 'BLOCKED',
                'evidence_locator': workload['evidence']['report_locator'],
            }
            for workload in contract['workloads']
        ]
    except Exception:
        contract = {'contract_id': None}
        contract_sha256 = None
        workloads = []
    document = {
        'schema_version': 1,
        'result_kind': 'aggregate-performance-qualification',
        'contract_id': contract.get('contract_id'),
        'contract_sha256': contract_sha256,
        'overall_status': 'FAIL',
        'validation_errors': [str(error)],
        'workloads': workloads,
        'company_performance_boundary': 'Repository performance evidence never marks the external CompanyQualification performance gate PASS.',
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, default=CONTRACT_PATH)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--contract-only', action='store_true')
    args = parser.parse_args()
    try:
        if args.contract_only:
            report = validate_contract_only(args.contract.resolve())
            print(json.dumps(report, sort_keys=True))
            return 0
        version_path = ROOT / 'VERSION'
        candidate_version = version_path.read_text(encoding='utf-8').strip() if version_path.is_file() else None
        report = build_qualification(contract_path=args.contract.resolve(), output=args.output.resolve(), candidate_version=candidate_version)
        print(json.dumps({'qualification': str(args.output.resolve().relative_to(ROOT)), 'status': report['overall_status']}))
        return 0
    except (OSError, PerformanceContractError, ValueError, KeyError, json.JSONDecodeError) as error:
        write_failure(args.output.resolve(), error, contract_path=args.contract.resolve())
        print(f'Performance result qualification FAILED: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
