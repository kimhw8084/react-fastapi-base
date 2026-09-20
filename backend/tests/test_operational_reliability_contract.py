from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.platform.settings import (
    CompanyOperationsEvidence,
    CompanyQualification,
    CompanyQualificationGate,
    EvidenceReference,
    OperationsDrillEvidence,
    OperationsFacts,
)


ROOT = Path(__file__).resolve().parents[2]


def drill(drill_id: str, *, status: str = 'BLOCKED_EXTERNAL') -> OperationsDrillEvidence:
    return OperationsDrillEvidence(
        drill_id=drill_id,
        status=status,
        evidence=([] if status != 'PASS' else [EvidenceReference(kind='operations_report', locator=f'evidence/company/{drill_id}.json', evidence_id=f'evidence-{drill_id}', issuer='company-operator')]),
        correlation_ids=[f'correlation-{drill_id}'],
        observed_at='2026-09-10T00:00:00Z',
        outcome='Sanitized company operations drill metadata.',
        reason_code='company_staging_required' if status != 'PASS' else 'drill_passed',
    )


def evidence(*, status: str = 'BLOCKED_EXTERNAL') -> CompanyOperationsEvidence:
    return CompanyOperationsEvidence(
        deployment_id='company-staging-1',
        candidate_version='1.0.0-rc.18',
        verified_source_commit='a' * 40,
        source_digest='b' * 64,
        operator_id='company-operator',
        created_at='2026-09-10T00:00:00Z',
        drills=[drill(identifier, status=status) for identifier in (
            'startup_restart', 'dependency_unavailable_recovery', 'database_readiness_degradation',
            'worker_crash_lease_recovery', 'outbound_integration_failure_retry', 'recovery_restore',
            'request_log_correlation',
        )],
    )


def test_external_operations_template_is_typed_and_unproven():
    template = json.loads((ROOT / 'deploy/company-operations-evidence.template.json').read_text())
    model = CompanyOperationsEvidence.model_validate(template)
    assert [drill_item.drill_id for drill_item in model.drills] == [
        'startup_restart', 'dependency_unavailable_recovery', 'database_readiness_degradation',
        'worker_crash_lease_recovery', 'outbound_integration_failure_retry', 'recovery_restore',
        'request_log_correlation',
    ]
    assert all(drill_item.status == 'BLOCKED_EXTERNAL' for drill_item in model.drills)


def test_external_operations_evidence_rejects_missing_categories_and_unsafe_locator():
    model = evidence()
    with pytest.raises(ValidationError):
        CompanyOperationsEvidence.model_validate({**model.model_dump(), 'drills': model.model_dump()['drills'][:-1]})
    with pytest.raises(ValidationError):
        EvidenceReference(kind='operations_report', locator='/private/operations.json', evidence_id='evidence-1', issuer='company-operator')
    with pytest.raises(ValidationError):
        EvidenceReference(kind='operations_report', locator='https://evidence.example/report?secret=bad', evidence_id='evidence-1', issuer='company-operator')


def test_blocked_or_unbound_operations_evidence_cannot_pass_operations_gate():
    facts = OperationsFacts(company_profile_evidence=True, operations_evidence=evidence())
    gate = CompanyQualificationGate(id='operations', status='PASS', evidence=[EvidenceReference(kind='operations_report', locator='evidence/company/operations.json', evidence_id='operations', issuer='company-operator')], facts=facts)
    gates = [
        CompanyQualificationGate(id='technical_release', status='BLOCKED', reason='not supplied'),
        CompanyQualificationGate(id='identity', status='BLOCKED', reason='not supplied'),
        CompanyQualificationGate(id='storage', status='BLOCKED', reason='not supplied'),
        CompanyQualificationGate(id='deployment', status='BLOCKED', reason='not supplied'),
        CompanyQualificationGate(id='ui_accessibility', status='BLOCKED', reason='not supplied'),
        CompanyQualificationGate(id='performance', status='BLOCKED', reason='not supplied'),
        gate,
        CompanyQualificationGate(id='release_evidence', status='BLOCKED', reason='not supplied'),
    ]
    # The complete company qualification contract performs the final gate
    # binding check; a repository aggregate is never an external PASS fact.
    assert any('unproven' in error for error in CompanyQualification(
        candidate_version='1.0.0-rc.18',
        verified_source_commit='a' * 40,
        source_digest='b' * 64,
        deployment_id='company-staging-1',
        identity_topology='per_user_process',
        storage_kind='local_disk',
        provider_sqlite_support_reference='provider-reference',
        all_database_clients_same_host=True,
        persistent_root='/company/root',
        gates=gates,
        approved_by='company-operator',
        approved_at='2026-09-10T00:00:00Z',
    ).contract_errors())
