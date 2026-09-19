from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.performance_contract import (
    CONTRACT_PATH,
    PerformanceContractError,
    load_contract,
    reconcile_reports,
    validate_contract,
)


SOURCE_COMMIT = 'a' * 40
SOURCE_DIGEST = 'b' * 64
CONTRACT_SHA = 'c' * 64


def valid_reports(contract: dict) -> dict[str, dict]:
    reports = {}
    for tier_id in ('owned-pure-algorithms', 'platform-data-volume', 'browser-ag-grid-scale'):
        rows = []
        for workload in [item for item in contract['workloads'] if item['tier_id'] == tier_id]:
            hard = {metric: 0.001 for metric in workload['hard_metrics']}
            diagnostic = {metric: None for metric in workload['diagnostic_metrics']}
            if tier_id != 'browser-ag-grid-scale':
                diagnostic['result'] = 1
                row = {
                    'id': workload['id'],
                    'status': 'PASS',
                    'scale': copy.deepcopy(workload['scale']),
                    'budgets': copy.deepcopy(workload['budgets']),
                    'hard_metrics': hard,
                    'diagnostic_metrics': diagnostic,
                    'evidence_locator': workload['evidence']['report_locator'],
                }
            else:
                hard.update({
                    'logical_rows': workload['scale']['logical_rows'],
                    'loaded_rows': workload['scale']['loaded_rows'],
                    'rendered_rows_before_deep_scroll': 20,
                    'rendered_rows_after_deep_scroll': 20,
                    'initial_readiness_ms': 100,
                })
                diagnostic['used_js_heap_bytes'] = None
                row = {
                    'id': workload['id'],
                    'status': 'PASS',
                    'scale': copy.deepcopy(workload['scale']),
                    'budgets': copy.deepcopy(workload['budgets']),
                    'hard_metrics': hard,
                    'diagnostic_metrics': diagnostic,
                    'evidence_locator': workload['evidence']['report_locator'],
                    'browser_project': 'chromium',
                    'viewport': contract['browser']['viewport'],
                }
                if workload['id'] == 'browser-ag-grid-virtualization-5000':
                    hard.update({
                        'rendered_row_ratio': 0.01,
                        'initial_rows_recycled': True,
                        'reached_target_row': True,
                        'selection_or_keyboard_works': True,
                        'representative_sort_works': True,
                        'deep_scroll_settle_ms': 100,
                        'sort_interaction_ms': 100,
                    })
                    row.update({
                        'row_recycling_proof': {'removed_after_deep_scroll': True},
                        'selection_result': {'selected_region': True},
                        'sort_result': {'first_row': 'Synthetic work item 0000'},
                    })
            rows.append(row)
        reports[tier_id] = {
            'schema_version': 2,
            'report_kind': 'performance-regression-result',
            'tier_id': tier_id,
            'contract_id': contract['contract_id'],
            'contract_sha256': CONTRACT_SHA,
            'source_commit': SOURCE_COMMIT,
            'source_digest': SOURCE_DIGEST,
            'result': 'PASS',
            'workloads': rows,
        }
    return reports


def reconcile(contract: dict, reports: dict[str, dict]) -> dict:
    return reconcile_reports(
        contract,
        reports,
        expected_source_commit=SOURCE_COMMIT,
        expected_source_digest=SOURCE_DIGEST,
        expected_contract_sha256=CONTRACT_SHA,
    )


def test_contract_is_canonical_and_machine_readable() -> None:
    contract, digest = load_contract(CONTRACT_PATH)
    assert contract['contract_id'] == 'project-os-performance-regression'
    assert len(contract['workloads']) == 19
    assert len(digest) == 64


def test_duplicate_workload_ids_fail_closed() -> None:
    contract, _ = load_contract(CONTRACT_PATH)
    contract['workloads'].append(copy.deepcopy(contract['workloads'][0]))
    with pytest.raises(PerformanceContractError, match='duplicate workload IDs'):
        validate_contract(contract)


def test_unknown_report_ids_fail_closed() -> None:
    contract, _ = load_contract(CONTRACT_PATH)
    reports = valid_reports(contract)
    reports['platform-data-volume']['workloads'][0]['id'] = 'unknown-workload'
    with pytest.raises(PerformanceContractError, match='unknown workload IDs'):
        reconcile(contract, reports)


def test_missing_applicable_workload_fails_closed() -> None:
    contract, _ = load_contract(CONTRACT_PATH)
    reports = valid_reports(contract)
    reports['owned-pure-algorithms']['workloads'].pop()
    with pytest.raises(PerformanceContractError, match='missing applicable workloads'):
        reconcile(contract, reports)


def test_changed_threshold_requires_matching_report_coverage() -> None:
    contract, _ = load_contract(CONTRACT_PATH)
    reports = valid_reports(contract)
    contract['workloads'][0]['budgets']['elapsed_seconds'] = 3.0
    with pytest.raises(PerformanceContractError, match='budget coverage'):
        reconcile(contract, reports)


def test_source_or_contract_sha_mismatch_fails_closed() -> None:
    contract, _ = load_contract(CONTRACT_PATH)
    reports = valid_reports(contract)
    reports['owned-pure-algorithms']['contract_sha256'] = 'd' * 64
    with pytest.raises(PerformanceContractError, match='contract SHA mismatch'):
        reconcile(contract, reports)
    reports = valid_reports(contract)
    reports['owned-pure-algorithms']['source_commit'] = 'e' * 40
    with pytest.raises(PerformanceContractError, match='source commit mismatch'):
        reconcile(contract, reports)


def test_browser_structural_interactions_and_timing_fail_closed() -> None:
    contract, _ = load_contract(CONTRACT_PATH)
    reports = valid_reports(contract)
    browser = reports['browser-ag-grid-scale']['workloads'][1]
    browser['hard_metrics']['rendered_rows_after_deep_scroll'] = 251
    with pytest.raises(PerformanceContractError, match='rendered row ceiling'):
        reconcile(contract, reports)

    reports = valid_reports(contract)
    browser = reports['browser-ag-grid-scale']['workloads'][1]
    browser['hard_metrics']['initial_rows_recycled'] = False
    with pytest.raises(PerformanceContractError, match='recycling proof'):
        reconcile(contract, reports)

    reports = valid_reports(contract)
    browser = reports['browser-ag-grid-scale']['workloads'][1]
    browser['hard_metrics']['selection_or_keyboard_works'] = False
    with pytest.raises(PerformanceContractError, match='interaction failed'):
        reconcile(contract, reports)

    reports = valid_reports(contract)
    browser = reports['browser-ag-grid-scale']['workloads'][1]
    browser['hard_metrics']['sort_interaction_ms'] = 5001
    with pytest.raises(PerformanceContractError, match='timing ceiling'):
        reconcile(contract, reports)


def test_optional_memory_null_is_valid_diagnostic_evidence() -> None:
    contract, _ = load_contract(CONTRACT_PATH)
    reports = valid_reports(contract)
    aggregate = reconcile(contract, reports)
    assert aggregate['overall_status'] == 'PASS'
    assert aggregate['workloads'][-1]['diagnostic_metrics']['used_js_heap_bytes'] is None
