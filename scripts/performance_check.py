#!/usr/bin/env python3
"""Run the canonical owned pure-algorithm performance regression tier."""
from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path
from typing import Any, Callable

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

from app.platform.statistics import (  # noqa: E402
    c_chart,
    correlation,
    cusum,
    descriptive,
    ewma,
    imr,
    linear_regression,
    p_chart,
    pareto,
    run_rule_flags,
)
from scripts.performance_contract import CONTRACT_PATH, load_contract, workloads_by_tier  # noqa: E402
from scripts.source_manifest import executable_source_commit, source_digest, source_hashes  # noqa: E402

OUTPUT = ROOT / 'evidence/current/performance/owned-algorithms.json'
TIER_ID = 'owned-pure-algorithms'


def measure(workload: dict[str, Any], operation: Callable[[], Any]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = operation()
        seconds = time.perf_counter() - started
        status = 'PASS' if seconds <= workload['budgets']['elapsed_seconds'] else 'FAIL'
        row = {
            'id': workload['id'],
            'status': status,
            'scale': workload['scale'],
            'budgets': workload['budgets'],
            'hard_metrics': {'elapsed_seconds': round(seconds, 6)},
            'diagnostic_metrics': {'result': result},
            'evidence_locator': workload['evidence']['report_locator'],
        }
        print(f"{status} {workload['id']}: {seconds:.3f}s <= {workload['budgets']['elapsed_seconds']:.3f}s")
        return row
    except Exception as error:  # pragma: no cover - failures remain visible in the report.
        print(f'FAIL {workload["id"]}: {error}')
        return {
            'id': workload['id'],
            'status': 'FAIL',
            'scale': workload['scale'],
            'budgets': workload['budgets'],
            'hard_metrics': {'elapsed_seconds': None},
            'diagnostic_metrics': {'result': None},
            'evidence_locator': workload['evidence']['report_locator'],
            'error': type(error).__name__,
        }


def main() -> int:
    contract, contract_sha256 = load_contract(CONTRACT_PATH)
    workloads = workloads_by_tier(contract, TIER_ID)
    by_id = {workload['id']: workload for workload in workloads}
    observations = int(by_id['descriptive-100k']['scale']['observations'])
    categories_count = int(by_id['pareto-100k']['scale']['categories'])
    sample_size = int(by_id['p-chart-100k']['scale']['samples_per_observation'])
    values = [100.0 + ((i % 97) - 48) * 0.013 + ((i % 7) - 3) * 0.002 for i in range(observations)]
    categories = [f'DEFECT-{i % categories_count:02d}' for i in range(observations)]
    defects = [i % 8 for i in range(observations)]
    samples = [sample_size] * observations

    operations: dict[str, Callable[[], Any]] = {
        'descriptive-100k': lambda: descriptive(values)['count'],
        'imr-100k': lambda: len(imr(values)['moving_ranges']),
        'ewma-100k': lambda: len(ewma(values)),
        'run-rules-100k': lambda: sum(len(value) for value in run_rule_flags(values).values()),
        'pareto-100k': lambda: len(pareto(categories)),
        'p-chart-100k': lambda: len(p_chart(defects, samples)['proportions']),
        'c-chart-100k': lambda: len(c_chart(defects)['counts']),
        'cusum-100k': lambda: len(cusum(values)['positive']),
        'correlation-100k': lambda: correlation(values, values),
        'regression-100k': lambda: linear_regression(values, values)['r_squared'],
    }
    rows = [measure(workload, operations[workload['id']]) for workload in workloads]
    source_hash_map = source_hashes()
    source_commit = executable_source_commit(ROOT)
    report = {
        'schema_version': 2,
        'report_kind': 'performance-regression-result',
        'tier_id': TIER_ID,
        'contract_id': contract['contract_id'],
        'contract_sha256': contract_sha256,
        'source_commit': source_commit,
        'source_digest': source_digest(source_hash_map),
        'command': ['python3', 'scripts/performance_check.py'],
        'environment': {'platform': platform.platform(), 'python': platform.python_version()},
        'result': 'PASS' if all(row['status'] == 'PASS' for row in rows) else 'FAIL',
        'workloads': rows,
        # Preserve the pre-CHG-35 machine-readable smoke-report fields for
        # existing tooling; the workload rows above remain canonical.
        'browser_render_budget_certified': False,
        'checks': [
            {
                'name': row['id'],
                'seconds': row['hard_metrics']['elapsed_seconds'],
                'budget_seconds': row['budgets']['elapsed_seconds'],
                'status': row['status'],
                'summary': row['diagnostic_metrics']['result'],
            }
            for row in rows
        ],
    }
    output = Path(os.environ.get('BASE_PERFORMANCE_ALGORITHMS_REPORT') or os.environ.get('BASE_PERFORMANCE_REPORT') or str(OUTPUT))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['result']} owned algorithm performance regression: {output}")
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
