from __future__ import annotations

from scripts.operational_diagnostics import safe_diagnostics_summary
from scripts.operational_reliability_contract import EXTERNAL_DRILL_IDS, REPOSITORY_SCENARIO_IDS, load_contract
from scripts import release_evidence


def test_operational_contract_has_stable_repository_and_external_ids():
    contract = load_contract()
    assert tuple(row['id'] for row in contract['repository_scenarios']) == REPOSITORY_SCENARIO_IDS
    assert tuple(row['id'] for row in contract['external_drill_categories']) == EXTERNAL_DRILL_IDS
    assert contract['evidence_policy']['production_ready'] is False


def test_repository_operations_result_remains_separate_from_company_gate():
    matrix = release_evidence.build_readiness_matrix(
        source_commit='a' * 40,
        source_digest='b' * 64,
        version='1.0.0-rc.18',
        results=[{'name': 'operational-reliability-qualification', 'status': 'PASS'}],
    )
    assert matrix['repository_operations']['status'] == 'PASS'
    operations_gate = next(row for row in matrix['gates'] if row['id'] == 'operations')
    assert operations_gate['status'] == 'BLOCKED'
    assert operations_gate['qualification_status'] == 'BLOCKED_EXTERNAL'
    assert matrix['production_ready'] is False


def test_safe_diagnostics_whitelists_status_metadata():
    summary = safe_diagnostics_summary({
        'candidate_version': '1.0.0-rc.18',
        'candidate_head': 'a' * 40,
        'executable_source_commit': 'b' * 40,
        'source_digest': 'c' * 64,
        'contract_id': 'react-fastapi-base.operational-reliability',
        'contract_revision': 1,
        'contract_sha256': 'd' * 64,
        'repository_operations_status': 'PASS',
        'company_operations_status': 'BLOCKED_EXTERNAL',
        'scenario_results': [{'id': 'OR-DIAGNOSTICS-SAFE-REDACTION', 'status': 'PASS', 'reason_code': 'diagnostic_redacted', 'raw_payload': 'not allowed'}],
        'external_blockers': [{'id': 'startup_restart', 'status': 'BLOCKED_EXTERNAL', 'reason_code': 'company_staging_required', 'private_root': '/not-returned'}],
    })
    assert 'raw_payload' not in str(summary)
    assert '/not-returned' not in str(summary)
    assert summary['production_ready'] is False
