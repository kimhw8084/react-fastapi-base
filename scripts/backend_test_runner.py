#!/usr/bin/env python3
"""Run the backend suite in deterministic parallel shards.

The backend suite is intentionally isolated per test through ``tmp_path`` but
can exceed the release verifier's wall-clock budget when run as one pytest
process on a developer Mac. Shards are assigned from sorted collected node IDs,
so the same source produces the same test partition on every run.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
import time
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def collect() -> list[str]:
    # Shard by file, not by parsed node IDs. Pytest's quiet collector omits
    # parameter values from node IDs, which would make parametrized tests fail
    # when selected directly. The repository's backend test files are the
    # stable, reviewable partition boundary.
    files = sorted(path.relative_to(BACKEND).as_posix() for path in (BACKEND / "tests").rglob("test_*.py"))
    if not files:
        raise RuntimeError("No backend test files were found.")
    return files


def run_shard(index: int, test_files: list[str], output: Path, timeout: int) -> tuple[int, str, float]:
    junit = output.with_name(f"{output.stem}.shard-{index + 1}.xml")
    junit.unlink(missing_ok=True)
    started = time.monotonic()
    command = [sys.executable, "-m", "pytest", "-q", *test_files, f"--junitxml={junit}"]
    try:
        result = subprocess.run(command, cwd=BACKEND, text=True, capture_output=True, timeout=timeout)
        combined = result.stdout + result.stderr
        return result.returncode, combined, time.monotonic() - started
    except subprocess.TimeoutExpired as error:
        output_text = (error.stdout or "") + (error.stderr or "")
        return 124, output_text + f"\nShard timed out after {timeout} seconds.\n", time.monotonic() - started


def merge_junit(output: Path, shard_paths: list[Path]) -> None:
    suite = ElementTree.Element("testsuite", {"name": "backend-sharded"})
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    for path in shard_paths:
        if not path.is_file():
            continue
        root = ElementTree.parse(path).getroot()
        suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
        for source in suites:
            for key in ("tests", "failures", "errors", "skipped"):
                totals[key] += int(source.attrib.get(key, "0"))
            totals["time"] += float(source.attrib.get("time", "0"))
            for child in list(source):
                suite.append(child)
    suite.attrib.update({key: str(value) for key, value in totals.items() if key != "time"})
    suite.set("time", f"{totals['time']:.3f}")
    output.parent.mkdir(parents=True, exist_ok=True)
    ElementTree.ElementTree(suite).write(output, encoding="utf-8", xml_declaration=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True, help="Merged JUnit XML output path.")
    parser.add_argument("--shards", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=240, help="Per-shard timeout in seconds.")
    args = parser.parse_args()
    if args.shards < 1 or args.timeout < 1:
        raise SystemExit("--shards and --timeout must be positive.")

    test_files = collect()
    shard_count = min(args.shards, len(test_files))
    shards = [[] for _ in range(shard_count)]
    for position, test_file in enumerate(test_files):
        shards[position % shard_count].append(test_file)
    print(f"Collected {len(test_files)} backend test files into {shard_count} deterministic shards.")

    with ThreadPoolExecutor(max_workers=shard_count) as executor:
        results = list(executor.map(
            lambda item: run_shard(item[0], item[1], args.output, args.timeout),
            enumerate(shards),
        ))
    shard_paths = [args.output.with_name(f"{args.output.stem}.shard-{index + 1}.xml") for index in range(shard_count)]
    merge_junit(args.output, shard_paths)
    failed = False
    for index, (exit_code, log, duration) in enumerate(results, start=1):
        print(f"--- backend shard {index} ({duration:.1f}s, exit {exit_code}) ---")
        print(log, end="")
        failed = failed or exit_code != 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
