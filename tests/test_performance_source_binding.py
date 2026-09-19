from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.e2e_runner import performance_source_binding
from scripts.performance_contract import PerformanceContractError
from scripts.performance_results import build_qualification


ROOT = Path(__file__).resolve().parents[1]
PERFORMANCE_REPORTS = {
    'owned-pure-algorithms': ROOT / 'evidence/current/performance/owned-algorithms.json',
    'platform-data-volume': ROOT / 'evidence/current/performance/stress.json',
    'browser-ag-grid-scale': ROOT / 'evidence/current/performance/browser.json',
}


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ['git', '-C', str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def evidence_only_head(tmp_path: Path) -> tuple[Path, str, str, str]:
    root = tmp_path / 'repo'
    (root / 'backend').mkdir(parents=True)
    (root / 'evidence').mkdir()
    git(root, 'init', '-q')
    git(root, 'config', 'user.email', 'performance-test@example.invalid')
    git(root, 'config', 'user.name', 'Performance Source Test')
    (root / 'backend' / 'source.py').write_text('VALUE = 1\n', encoding='utf-8')
    git(root, 'add', 'backend/source.py')
    git(root, 'commit', '-qm', 'executable source')
    source_commit = git(root, 'rev-parse', 'HEAD')
    source_digest_before = performance_source_binding(root)[1]
    (root / 'evidence' / 'binding.json').write_text('{"evidence": true}\n', encoding='utf-8')
    git(root, 'add', 'evidence/binding.json')
    git(root, 'commit', '-qm', 'evidence-only binding')
    head = git(root, 'rev-parse', 'HEAD')
    return root, source_commit, source_digest_before, head


def copied_reports(tmp_path: Path, source_commit: str, source_digest: str) -> dict[str, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for tier_id, source_path in PERFORMANCE_REPORTS.items():
        report = json.loads(source_path.read_text(encoding='utf-8'))
        report['source_commit'] = source_commit
        report['source_digest'] = source_digest
        path = tmp_path / f'{tier_id}.json'
        path.write_text(json.dumps(report) + '\n', encoding='utf-8')
        paths[tier_id] = path
    return paths


def test_browser_binding_uses_executable_source_after_evidence_only_head(tmp_path: Path) -> None:
    root, source_commit, source_digest, head = evidence_only_head(tmp_path)

    bound_commit, bound_digest = performance_source_binding(root)

    assert head != source_commit
    assert bound_commit == source_commit
    assert bound_digest == source_digest


def test_evidence_only_head_aggregate_passes_and_wrong_source_fails_closed(tmp_path: Path) -> None:
    root, source_commit, source_digest, head = evidence_only_head(tmp_path)
    assert head != source_commit
    reports = copied_reports(tmp_path, source_commit, source_digest)

    qualification = build_qualification(
        report_paths=reports,
        output=tmp_path / 'qualification.json',
        expected_source_commit=source_commit,
        expected_source_digest=source_digest,
    )

    assert qualification['overall_status'] == 'PASS'
    browser_report = json.loads(reports['browser-ag-grid-scale'].read_text(encoding='utf-8'))
    assert browser_report['source_commit'] == source_commit

    wrong_reports = copied_reports(tmp_path / 'wrong', 'f' * 40, source_digest)
    with pytest.raises(PerformanceContractError, match='source commit mismatch'):
        build_qualification(
            report_paths=wrong_reports,
            output=tmp_path / 'wrong-qualification.json',
            expected_source_commit=source_commit,
            expected_source_digest=source_digest,
        )
