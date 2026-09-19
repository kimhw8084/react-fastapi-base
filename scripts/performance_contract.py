"""Canonical performance regression contract and report reconciliation."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / 'contracts/performance-regression.json'
CONTRACT_ID = 'project-os-performance-regression'
REPORT_SCHEMA_VERSION = 2
TIER_IDS = ('owned-pure-algorithms', 'platform-data-volume', 'browser-ag-grid-scale')
CURRENT_WORKLOAD_IDS = {
    'owned-pure-algorithms': (
        'descriptive-100k', 'imr-100k', 'ewma-100k', 'run-rules-100k',
        'pareto-100k', 'p-chart-100k', 'c-chart-100k', 'cusum-100k',
        'correlation-100k', 'regression-100k',
    ),
    'platform-data-volume': (
        'table-100k-filter-sort', 'planning-5000-dependencies',
        'graph-10000-nodes-20000-edges', 'rack-100-racks-20000-connections',
        'wafer-100k-die-map', 'observability-100k-events',
        'dashboard-1000-widgets-layout',
    ),
    'browser-ag-grid-scale': (
        'browser-server-page-100k-50', 'browser-ag-grid-virtualization-5000',
    ),
}
SHA256_PATTERN = re.compile(r'^[0-9a-f]{64}$')
COMMIT_PATTERN = re.compile(r'^[0-9a-f]{40}$')


class PerformanceContractError(ValueError):
    """Raised when a performance contract or result is not safe to qualify."""


def _strict_json(path: Path) -> dict[str, Any]:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PerformanceContractError(f'{path} contains duplicate JSON field {key!r}.')
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=object_pairs)
    except (OSError, json.JSONDecodeError) as error:
        raise PerformanceContractError(f'Cannot read valid performance JSON from {path}: {error}') from error
    if not isinstance(value, dict):
        raise PerformanceContractError(f'{path} must contain a JSON object.')
    return value


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise PerformanceContractError(f'Cannot hash performance evidence {path}: {error}') from error


def load_contract(path: Path = CONTRACT_PATH) -> tuple[dict[str, Any], str]:
    document = _strict_json(path)
    validate_contract(document)
    return document, sha256_file(path)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PerformanceContractError(message)


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)), f'{label} must be a finite number.')
    result = float(value)
    if positive:
        _require(result > 0, f'{label} must be greater than zero.')
    return result


def validate_contract(contract: dict[str, Any]) -> None:
    _require(contract.get('schema_version') == 1, 'Performance contract schema_version must be 1.')
    _require(contract.get('contract_id') == CONTRACT_ID, 'Performance contract has an unexpected contract_id.')
    _require(contract.get('contract_revision') == 1, 'Performance contract contract_revision must be 1.')
    tiers = contract.get('tiers')
    _require(isinstance(tiers, list), 'Performance contract tiers must be a list.')
    _require(all(isinstance(tier, dict) for tier in tiers), 'Performance contract tiers must be objects.')
    _require([tier.get('id') for tier in tiers] == list(TIER_IDS), 'Performance contract must enumerate exactly the three canonical tiers in order.')
    tier_runners = {}
    for tier in tiers:
        _require(isinstance(tier, dict), 'Performance contract tiers must be objects.')
        tier_id = tier.get('id')
        _require(isinstance(tier_id, str) and tier_id in TIER_IDS, f'Unknown performance tier: {tier_id!r}.')
        _require(tier_id not in tier_runners, f'Duplicate performance tier: {tier_id}.')
        _require(isinstance(tier.get('runner'), str) and tier['runner'], f'{tier_id} must declare a runner.')
        tier_runners[tier_id] = tier['runner']

    browser = contract.get('browser')
    _require(isinstance(browser, dict), 'Performance contract must declare browser settings.')
    _require(browser.get('project') == 'chromium', 'Browser performance qualification must use the chromium project.')
    viewport = browser.get('viewport')
    _require(isinstance(viewport, dict), 'Browser performance contract must declare a fixed viewport.')
    _number(viewport.get('width'), 'browser.viewport.width', positive=True)
    _number(viewport.get('height'), 'browser.viewport.height', positive=True)
    grouped = browser.get('grouped_grid_strategy')
    _require(isinstance(grouped, dict), 'GroupedSemanticGrid strategy must be documented.')
    _require(grouped.get('component') == 'GroupedSemanticGrid', 'Grouped grid strategy must name GroupedSemanticGrid.')
    _require(grouped.get('virtualization_claim') is False, 'GroupedSemanticGrid must not claim virtualization.')
    _require(grouped.get('scale_strategy') == 'server-page-bounded', 'GroupedSemanticGrid must remain server-page bounded.')

    workloads = contract.get('workloads')
    _require(isinstance(workloads, list) and workloads, 'Performance contract workloads must be a non-empty list.')
    ids = [item.get('id') if isinstance(item, dict) else None for item in workloads]
    _require(len(ids) == len(set(ids)), 'Performance contract contains duplicate workload IDs.')
    _require(set(ids) == set(value for values in CURRENT_WORKLOAD_IDS.values() for value in values), 'Performance contract workload inventory must preserve the current algorithm, stress and browser workload set.')
    by_id: dict[str, dict[str, Any]] = {}
    for workload in workloads:
        _require(isinstance(workload, dict), 'Performance contract workloads must be objects.')
        workload_id = workload.get('id')
        _require(isinstance(workload_id, str) and workload_id, 'Performance workload IDs must be non-empty strings.')
        tier_id = workload.get('tier_id')
        _require(tier_id in TIER_IDS, f'{workload_id} names an unknown tier {tier_id!r}.')
        _require(workload.get('applicability') == 'required', f'{workload_id} must be required and applicable.')
        _require(isinstance(workload.get('scale'), dict) and workload['scale'], f'{workload_id} must declare an explicit scale.')
        for key, value in workload['scale'].items():
            _number(value, f'{workload_id}.scale.{key}', positive=True)
        budgets = workload.get('budgets')
        _require(isinstance(budgets, dict) and budgets, f'{workload_id} must declare explicit budgets.')
        for key, value in budgets.items():
            _number(value, f'{workload_id}.budgets.{key}', positive=True)
        for metric_group in ('hard_metrics', 'diagnostic_metrics'):
            metrics = workload.get(metric_group)
            _require(isinstance(metrics, list) and metrics and len(metrics) == len(set(metrics)), f'{workload_id}.{metric_group} must be a unique non-empty list.')
            _require(all(isinstance(value, str) and value for value in metrics), f'{workload_id}.{metric_group} must contain metric names.')
        evidence = workload.get('evidence')
        _require(isinstance(evidence, dict) and isinstance(evidence.get('report_locator'), str) and evidence['report_locator'].startswith('evidence/current/performance/'), f'{workload_id} must declare a performance evidence locator.')
        if tier_id == 'browser-ag-grid-scale':
            _require(isinstance(workload.get('invariants'), dict) and workload['invariants'], f'{workload_id} must declare browser structural invariants.')
            if workload_id == 'browser-ag-grid-virtualization-5000':
                _require(workload.get('fixture_kind') == 'synthetic-test-only', 'The large loaded browser fixture must be labeled synthetic/test-only.')
                _require('initial_rows_recycled' in workload['hard_metrics'], f'{workload_id} must require row recycling proof.')
                _require('selection_or_keyboard_works' in workload['hard_metrics'], f'{workload_id} must require deep-row interaction proof.')
                _require('representative_sort_works' in workload['hard_metrics'], f'{workload_id} must require representative sort proof.')
        by_id[workload_id] = workload

    for tier_id, expected_ids in CURRENT_WORKLOAD_IDS.items():
        actual = [workload_id for workload_id in ids if by_id[workload_id]['tier_id'] == tier_id]
        _require(set(actual) == set(expected_ids), f'{tier_id} workload inventory is incomplete or contains an unexpected workload.')
        _require(tier_runners[tier_id], f'{tier_id} has no executable runner.')


def workloads_by_tier(contract: dict[str, Any], tier_id: str) -> list[dict[str, Any]]:
    validate_contract(contract)
    return [workload for workload in contract['workloads'] if workload['tier_id'] == tier_id]


def _require_sha(value: Any, label: str, pattern: re.Pattern[str]) -> None:
    _require(isinstance(value, str) and pattern.fullmatch(value) is not None, f'{label} must be a full lowercase SHA.')


def _validate_browser_row(workload: dict[str, Any], row: dict[str, Any], browser: dict[str, Any]) -> None:
    hard = row.get('hard_metrics')
    diagnostic = row.get('diagnostic_metrics')
    _require(isinstance(hard, dict) and set(hard) == set(workload['hard_metrics']), f'{workload["id"]} hard metrics do not exactly match the contract.')
    _require(isinstance(diagnostic, dict) and set(diagnostic) == set(workload['diagnostic_metrics']), f'{workload["id"]} diagnostic metrics do not exactly match the contract.')
    scale = workload['scale']
    _require('logical_rows' in hard and 'loaded_rows' in hard, f'{workload["id"]} must report logical and loaded row counts.')
    _require(hard['logical_rows'] == scale['logical_rows'], f'{workload["id"]} logical row scale drifted from the contract.')
    _require(hard['loaded_rows'] == scale['loaded_rows'], f'{workload["id"]} loaded row scale drifted from the contract.')
    invariants = workload['invariants']
    for key in ('rendered_rows_before_deep_scroll', 'rendered_rows_after_deep_scroll'):
        _number(hard[key], f'{workload["id"]}.{key}')
        _require(hard[key] <= invariants['rendered_row_ceiling'], f'{workload["id"]} exceeds the rendered row ceiling.')
    viewport = row.get('viewport')
    _require(viewport == browser['viewport'], f'{workload["id"]} viewport does not match the fixed contract viewport.')
    _require(row.get('browser_project') == browser['project'], f'{workload["id"]} browser project identity drifted.')
    if workload['id'] == 'browser-ag-grid-virtualization-5000':
        _number(hard['rendered_row_ratio'], f'{workload["id"]}.rendered_row_ratio')
        _require(hard['rendered_row_ratio'] <= invariants['rendered_row_fraction_ceiling'], f'{workload["id"]} rendered row ratio is not a small fraction of loaded rows.')
        _require(hard['initial_rows_recycled'] is True, f'{workload["id"]} is missing initial-row recycling proof.')
        _require(hard['reached_target_row'] is True, f'{workload["id"]} did not reach the deep target row.')
        _require(hard['selection_or_keyboard_works'] is True, f'{workload["id"]} deep selection/keyboard interaction failed.')
        _require(hard['representative_sort_works'] is True, f'{workload["id"]} representative sort interaction failed.')
    for metric, budget in workload['budgets'].items():
        _number(hard[metric], f'{workload["id"]}.{metric}')
        _require(hard[metric] <= budget, f'{workload["id"]} timing ceiling {metric} was exceeded.')
    heap = diagnostic.get('used_js_heap_bytes')
    _require(heap is None or (isinstance(heap, int) and not isinstance(heap, bool) and heap >= 0), f'{workload["id"]} optional heap diagnostics must be a non-negative integer or null.')


def reconcile_reports(
    contract: dict[str, Any],
    reports: dict[str, dict[str, Any]],
    *,
    expected_source_commit: str,
    expected_source_digest: str,
    expected_contract_sha256: str,
    report_locators: dict[str, str] | None = None,
    report_hashes: dict[str, str] | None = None,
    candidate_version: str | None = None,
) -> dict[str, Any]:
    validate_contract(contract)
    _require_sha(expected_source_commit, 'expected_source_commit', COMMIT_PATTERN)
    _require_sha(expected_source_digest, 'expected_source_digest', SHA256_PATTERN)
    _require_sha(expected_contract_sha256, 'expected_contract_sha256', SHA256_PATTERN)
    report_locators = report_locators or {}
    report_hashes = report_hashes or {}
    by_id = {workload['id']: workload for workload in contract['workloads']}
    aggregate_rows: list[dict[str, Any]] = []
    aggregate_reports: dict[str, dict[str, Any]] = {}
    for tier_id in TIER_IDS:
        report = reports.get(tier_id)
        _require(isinstance(report, dict), f'Missing applicable performance report for tier {tier_id}.')
        _require(report.get('schema_version') == REPORT_SCHEMA_VERSION, f'{tier_id} report schema_version is unsupported.')
        _require(report.get('report_kind') == 'performance-regression-result', f'{tier_id} report kind is invalid.')
        _require(report.get('tier_id') == tier_id, f'{tier_id} report tier binding is invalid.')
        _require(report.get('contract_id') == contract['contract_id'], f'{tier_id} report contract ID mismatch.')
        _require(report.get('contract_sha256') == expected_contract_sha256, f'{tier_id} report contract SHA mismatch.')
        _require(report.get('source_commit') == expected_source_commit, f'{tier_id} report source commit mismatch.')
        _require(report.get('source_digest') == expected_source_digest, f'{tier_id} report source digest mismatch.')
        _require(report.get('result') == 'PASS', f'{tier_id} performance report is not PASS.')
        expected = [workload['id'] for workload in contract['workloads'] if workload['tier_id'] == tier_id]
        rows = report.get('workloads')
        _require(isinstance(rows, list), f'{tier_id} report workloads must be a list.')
        actual = [row.get('id') if isinstance(row, dict) else None for row in rows]
        _require(len(actual) == len(set(actual)), f'{tier_id} report contains duplicate workload IDs.')
        unknown = sorted(set(actual) - set(expected))
        _require(not unknown, f'{tier_id} report references unknown workload IDs: {", ".join(unknown)}.')
        missing = sorted(set(expected) - set(actual))
        _require(not missing, f'{tier_id} report is missing applicable workloads: {", ".join(missing)}.')
        ordered_rows = {row['id']: row for row in rows}
        for workload_id in expected:
            workload = by_id[workload_id]
            row = ordered_rows[workload_id]
            _require(row.get('status') == 'PASS', f'{workload_id} result is not PASS.')
            _require(row.get('scale') == workload['scale'], f'{workload_id} scale does not match the canonical contract.')
            _require(row.get('budgets') == workload['budgets'], f'{workload_id} executable/result budget coverage does not match the canonical contract.')
            _require(row.get('evidence_locator') == workload['evidence']['report_locator'], f'{workload_id} evidence locator does not match the canonical contract.')
            if tier_id == 'browser-ag-grid-scale':
                _validate_browser_row(workload, row, contract['browser'])
            else:
                hard = row.get('hard_metrics')
                diagnostic = row.get('diagnostic_metrics')
                _require(isinstance(hard, dict) and set(hard) == set(workload['hard_metrics']), f'{workload_id} hard metrics do not exactly match the contract.')
                _require(isinstance(diagnostic, dict) and set(diagnostic) == set(workload['diagnostic_metrics']), f'{workload_id} diagnostic metrics do not exactly match the contract.')
                _number(hard['elapsed_seconds'], f'{workload_id}.elapsed_seconds')
                _require(hard['elapsed_seconds'] <= workload['budgets']['elapsed_seconds'], f'{workload_id} exceeded its generous timing ceiling.')
            aggregate_row = {
                'id': workload_id,
                'tier_id': tier_id,
                'scale': workload['scale'],
                'budgets': workload['budgets'],
                'status': row['status'],
                'hard_metrics': row['hard_metrics'],
                'diagnostic_metrics': row['diagnostic_metrics'],
                'evidence_locator': row['evidence_locator'],
            }
            if tier_id == 'browser-ag-grid-scale':
                for key in ('fixture_kind', 'browser_project', 'viewport', 'row_recycling_proof', 'selection_result', 'sort_result'):
                    if key in row:
                        aggregate_row[key] = row[key]
            aggregate_rows.append(aggregate_row)
        aggregate_reports[tier_id] = {
            'locator': report_locators.get(tier_id),
            'sha256': report_hashes.get(tier_id),
        }
    return {
        'schema_version': 1,
        'result_kind': 'aggregate-performance-qualification',
        'contract_id': contract['contract_id'],
        'contract_sha256': expected_contract_sha256,
        'source_commit': expected_source_commit,
        'source_digest': expected_source_digest,
        'candidate_version': candidate_version,
        'overall_status': 'PASS',
        'reports': aggregate_reports,
        'required_workload_ids': [workload['id'] for workload in contract['workloads']],
        'workloads': aggregate_rows,
        'company_performance_boundary': 'Repository performance PASS is not CompanyQualification performance PASS; authentic company/profile production-like evidence remains external and BLOCKED.',
    }
