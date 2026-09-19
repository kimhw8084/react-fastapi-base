from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from scripts.e2e_runner import performance_source_identity
from scripts.performance_contract import CONTRACT_PATH, PerformanceContractError, load_contract
from scripts.performance_results import build_qualification
from scripts.source_manifest import source_digest, source_hashes

from tests.test_performance_contract import valid_reports


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(['git', *args], cwd=repo, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


def source_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / 'repo'
    for directory in ('backend', 'frontend', 'contracts', 'scripts', 'tests', 'experience-lab', 'catalog'):
        (repo / directory).mkdir(parents=True)
    (repo / 'backend/app.py').write_text('VALUE = 1\n')
    (repo / 'frontend/app.ts').write_text('export const value = 1\n')
    (repo / 'contracts/api.json').write_text('{}\n')
    (repo / 'scripts/runner.py').write_text('print("run")\n')
    (repo / 'tests/test_app.py').write_text('def test_app(): pass\n')
    (repo / 'experience-lab/widget.ts').write_text('export const widget = true\n')
    (repo / 'catalog/roadmap.json').write_text('{}\n')
    (repo / 'dev').write_text('#!/bin/sh\n')
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 'performance-test@example.invalid')
    git(repo, 'config', 'user.name', 'Performance source binding test')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'executable source')
    source_commit = git(repo, 'rev-parse', 'HEAD')
    source_digest_value = source_digest(source_hashes(repo))

    (repo / 'evidence/current/performance').mkdir(parents=True)
    (repo / 'evidence/current/performance/browser.json').write_text('{"result":"PASS"}\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'evidence binding')
    assert git(repo, 'rev-parse', 'HEAD') != source_commit
    return repo, source_commit, source_digest_value


def write_reports(tmp_path: Path, reports: dict[str, dict]) -> dict[str, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    paths = {}
    for tier_id, report in reports.items():
        path = tmp_path / f'{tier_id}.json'
        path.write_text(json.dumps(report) + '\n')
        paths[tier_id] = path
    return paths


def test_browser_identity_uses_executable_source_after_evidence_binding_and_qualifies(tmp_path: Path):
    repo, source_commit, expected_digest = source_repo(tmp_path)
    assert performance_source_identity(repo) == (source_commit, expected_digest)

    contract, contract_sha = load_contract(CONTRACT_PATH)
    reports = valid_reports(contract)
    for report in reports.values():
        report['contract_sha256'] = contract_sha
        report['source_commit'] = source_commit
        report['source_digest'] = expected_digest
    qualification = build_qualification(
        contract_path=CONTRACT_PATH,
        report_paths=write_reports(tmp_path / 'reports', reports),
        output=tmp_path / 'qualification.json',
        expected_source_commit=source_commit,
        expected_source_digest=expected_digest,
    )
    assert qualification['overall_status'] == 'PASS'
    assert qualification['source_commit'] == source_commit
    assert qualification['source_digest'] == expected_digest


def test_wrong_browser_source_commit_fails_closed_after_evidence_binding(tmp_path: Path):
    repo, source_commit, expected_digest = source_repo(tmp_path)
    contract, contract_sha = load_contract(CONTRACT_PATH)
    reports = valid_reports(contract)
    for report in reports.values():
        report['contract_sha256'] = contract_sha
        report['source_commit'] = source_commit
        report['source_digest'] = expected_digest
    reports['browser-ag-grid-scale'] = copy.deepcopy(reports['browser-ag-grid-scale'])
    reports['browser-ag-grid-scale']['source_commit'] = 'e' * 40

    with pytest.raises(PerformanceContractError, match='source commit mismatch'):
        build_qualification(
            contract_path=CONTRACT_PATH,
            report_paths=write_reports(tmp_path / 'reports', reports),
            output=tmp_path / 'qualification.json',
            expected_source_commit=source_commit,
            expected_source_digest=expected_digest,
        )
