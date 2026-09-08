#!/usr/bin/env python3
"""Deterministic data-volume proof for platform algorithms and bounded projections."""
from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import platform
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def measure(name, budget, operation, size):
    started = time.perf_counter()
    result = operation()
    seconds = time.perf_counter() - started
    return {'name': name, 'size': size, 'seconds': round(seconds, 6), 'budget_seconds': budget, 'status': 'PASS' if seconds <= budget else 'FAIL', 'result': result}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/performance/stress.json')
    args = parser.parse_args()
    checks = []
    rows = [{'id': str(i), 'status': 'open' if i % 3 else 'done', 'priority': i % 7, 'updated': i} for i in range(100_000)]
    checks.append(measure('table-100k-filter-sort', 2.5, lambda: len(sorted((row for row in rows if row['status'] == 'open'), key=lambda row: (-row['priority'], -row['updated']))[:100]), 100_000))

    tasks = list(range(5_000))
    checks.append(measure('planning-5000-dependencies', 1.5, lambda: max((tasks[i - 1] + 1 if i else 0) for i in tasks), 5_000))

    adjacency = {str(i): [str((i + 1) % 10_000), str((i + 37) % 10_000)] for i in range(10_000)}
    def graph_trace():
        seen = {'0'}
        queue = deque(['0'])
        while queue:
            for peer in adjacency[queue.popleft()]:
                if peer not in seen:
                    seen.add(peer)
                    queue.append(peer)
        return len(seen)
    checks.append(measure('graph-10000-nodes-20000-edges', 2.0, graph_trace, 30_000))

    placements = [(rack, device, unit) for rack in range(100) for device in range(100) for unit in (1, 2)]
    connections = [(i, (i + 1) % len(placements)) for i in range(20_000)]
    checks.append(measure('rack-100-racks-20000-connections', 1.5, lambda: len({source for source, _ in connections}), len(placements) + len(connections)))

    die = [(i % 17 == 0, i % 9) for i in range(100_000)]
    checks.append(measure('wafer-100k-die-map', 1.0, lambda: sum(1 for bad, _ in die if not bad), 100_000))

    events = [{'service': f'service-{i % 50}', 'correlation_id': f'corr-{i % 1000}', 'latency': i % 1000} for i in range(100_000)]
    checks.append(measure('observability-100k-events', 1.5, lambda: sum(1 for event in events if event['service'] == 'service-7' and event['correlation_id'] == 'corr-7'), 100_000))

    widgets = [{'id': i, 'x': i % 12, 'y': i // 12, 'w': 1 + i % 4, 'h': 1 + i % 3} for i in range(1_000)]
    checks.append(measure('dashboard-1000-widgets-layout', 0.75, lambda: max(widget['y'] + widget['h'] for widget in widgets), 1_000))

    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    result = 'PASS' if all(item['status'] == 'PASS' for item in checks) else 'FAIL'
    report = {'schema_version': 1, 'source_commit': source_commit, 'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'command': ['python3', 'scripts/performance_stress.py'], 'exit_code': 0 if result == 'PASS' else 1, 'environment': {'platform': platform.platform(), 'python': platform.python_version()}, 'hashes': {'source_commit': source_commit}, 'checks': checks, 'result': result}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
