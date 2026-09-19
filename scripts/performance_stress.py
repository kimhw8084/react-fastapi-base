#!/usr/bin/env python3
"""Run the canonical deterministic platform data-volume regression tier."""
from __future__ import annotations

import argparse
import json
import platform
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.performance_contract import CONTRACT_PATH, load_contract, workloads_by_tier  # noqa: E402
from scripts.source_manifest import executable_source_commit, source_digest, source_hashes  # noqa: E402

TIER_ID = 'platform-data-volume'


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
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/performance/stress.json')
    args = parser.parse_args()
    contract, contract_sha256 = load_contract(CONTRACT_PATH)
    workloads = workloads_by_tier(contract, TIER_ID)
    by_id = {workload['id']: workload for workload in workloads}

    rows = [
        {'id': i, 'status': 'open' if i % 3 else 'done', 'priority': i % 7, 'updated': i}
        for i in range(int(by_id['table-100k-filter-sort']['scale']['rows']))
    ]
    tasks = list(range(int(by_id['planning-5000-dependencies']['scale']['tasks'])))
    node_count = int(by_id['graph-10000-nodes-20000-edges']['scale']['nodes'])
    adjacency = {str(i): [str((i + 1) % node_count), str((i + 37) % node_count)] for i in range(node_count)}

    def graph_trace() -> int:
        seen = {'0'}
        queue = deque(['0'])
        while queue:
            for peer in adjacency[queue.popleft()]:
                if peer not in seen:
                    seen.add(peer)
                    queue.append(peer)
        return len(seen)

    placements = [
        (rack, device, unit)
        for rack in range(int(by_id['rack-100-racks-20000-connections']['scale']['racks']))
        for device in range(int(by_id['rack-100-racks-20000-connections']['scale']['devices_per_rack']))
        for unit in (1, 2)
    ]
    connection_count = int(by_id['rack-100-racks-20000-connections']['scale']['connections'])
    connections = [(i, (i + 1) % len(placements)) for i in range(connection_count)]
    die = [(i % 17 == 0, i % 9) for i in range(int(by_id['wafer-100k-die-map']['scale']['die']))]
    event_scale = by_id['observability-100k-events']['scale']
    events = [
        {'service': f"service-{i % int(event_scale['services'])}", 'correlation_id': f"corr-{i % int(event_scale['correlation_ids'])}", 'latency': i % 1000}
        for i in range(int(event_scale['events']))
    ]
    widgets = [
        {'id': i, 'x': i % 12, 'y': i // 12, 'w': 1 + i % 4, 'h': 1 + i % 3}
        for i in range(int(by_id['dashboard-1000-widgets-layout']['scale']['widgets']))
    ]
    operations: dict[str, Callable[[], Any]] = {
        'table-100k-filter-sort': lambda: len(sorted((row for row in rows if row['status'] == 'open'), key=lambda row: (-row['priority'], -row['updated']))[:int(by_id['table-100k-filter-sort']['scale']['returned_rows'])]),
        'planning-5000-dependencies': lambda: max((tasks[i - 1] + 1 if i else 0) for i in tasks),
        'graph-10000-nodes-20000-edges': graph_trace,
        'rack-100-racks-20000-connections': lambda: len({source for source, _ in connections}),
        'wafer-100k-die-map': lambda: sum(1 for bad, _ in die if not bad),
        'observability-100k-events': lambda: sum(1 for event in events if event['service'] == 'service-7' and event['correlation_id'] == 'corr-7'),
        'dashboard-1000-widgets-layout': lambda: max(widget['y'] + widget['h'] for widget in widgets),
    }
    report_rows = [measure(workload, operations[workload['id']]) for workload in workloads]
    source_hash_map = source_hashes()
    report = {
        'schema_version': 2,
        'report_kind': 'performance-regression-result',
        'tier_id': TIER_ID,
        'contract_id': contract['contract_id'],
        'contract_sha256': contract_sha256,
        'source_commit': executable_source_commit(ROOT),
        'source_digest': source_digest(source_hash_map),
        'command': ['python3', 'scripts/performance_stress.py'],
        'environment': {'platform': platform.platform(), 'python': platform.python_version()},
        'result': 'PASS' if all(row['status'] == 'PASS' for row in report_rows) else 'FAIL',
        'workloads': report_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['result']} platform data-volume performance regression: {args.output}")
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
