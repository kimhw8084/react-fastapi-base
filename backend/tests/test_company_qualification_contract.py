from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.platform.settings import (
    CompanyQualification,
    CompanyQualificationGate,
    DeploymentFacts,
    EvidenceReference,
    IdentityFacts,
    OperationsFacts,
    PerformanceFacts,
    REPOSITORY_RELEASE_IDENTITY_PATH,
    RepositoryReleaseIdentity,
    RepositorySourceEvidence,
    ReleaseEvidenceFacts,
    Settings,
    StorageFacts,
    TechnicalReleaseFacts,
    UiAccessibilityFacts,
    load_company_qualification,
    load_repository_release_identity,
)
from app.platform.version import VERSION


def evidence(kind: str, name: str) -> EvidenceReference:
    return EvidenceReference(kind=kind, locator=f'evidence/company/{name}.json', evidence_id=f'fixture-{name}', issuer='fixture-operator')


def repository_identity() -> RepositoryReleaseIdentity:
    try:
        return load_repository_release_identity()
    except ValueError:
        return RepositoryReleaseIdentity(
            identity_type='repository_rc11_release',
            project='react-fastapi-base',
            profile='company',
            candidate_version=VERSION,
            verified_source_commit='a' * 40,
            source_digest='b' * 64,
            source_evidence=RepositorySourceEvidence(locator='evidence/test/source-hashes.json', sha256='c' * 64),
            verification=RepositorySourceEvidence(locator='evidence/test/verification.json', sha256='d' * 64),
            generated_by='scripts/generate_release_identity.py',
            code_ready=True,
            production_ready=False,
            release_status='NOT_CERTIFIED',
        )


def qualified(root: Path, *, source_commit: str | None = None, source_digest: str | None = None) -> CompanyQualification:
    expected = repository_identity()
    source_commit = expected.verified_source_commit if source_commit is None else source_commit
    source_digest = expected.source_digest if source_digest is None else source_digest
    return CompanyQualification(
        candidate_version=VERSION,
        verified_source_commit=source_commit,
        source_digest=source_digest,
        deployment_id='deployment-1',
        identity_topology='per_user_process',
        storage_kind='local_disk',
        provider_sqlite_support_reference='provider-record-1',
        all_database_clients_same_host=True,
        persistent_root=str(root.resolve()),
        approved_by='release-operator',
        approved_at='2026-09-10T00:00:00Z',
        gates=[
            CompanyQualificationGate(id='technical_release', status='PASS', evidence=[evidence('verification_report', 'technical')], facts=TechnicalReleaseFacts(code_ready=True, candidate_version=VERSION, verified_source_commit=source_commit, source_digest=source_digest)),
            CompanyQualificationGate(id='identity', status='PASS', evidence=[evidence('identity_proof', 'identity')], facts=IdentityFacts(identity_topology='per_user_process', simultaneous_real_user_evidence=True)),
            CompanyQualificationGate(id='storage', status='PASS', evidence=[evidence('storage_proof', 'storage')], facts=StorageFacts(storage_kind='local_disk', provider_sqlite_support_reference='provider-record-1', all_database_clients_same_host=True, persistent_root=str(root.resolve()))),
            CompanyQualificationGate(id='deployment', status='PASS', evidence=[evidence('deployment_proof', 'deployment')], facts=DeploymentFacts(deployment_id='deployment-1', ingress_authentication_evidence=True, redeploy_persistence_evidence=evidence('deployment_proof', 'redeploy'), restore_drill_evidence=evidence('deployment_proof', 'restore'))),
            CompanyQualificationGate(id='ui_accessibility', status='PASS', evidence=[evidence('accessibility_report', 'accessibility')], facts=UiAccessibilityFacts(company_profile_evidence=True)),
            CompanyQualificationGate(id='performance', status='PASS', evidence=[evidence('performance_report', 'performance')], facts=PerformanceFacts(company_profile_evidence=True)),
            CompanyQualificationGate(id='operations', status='PASS', evidence=[evidence('operations_report', 'operations')], facts=OperationsFacts(company_profile_evidence=True)),
            CompanyQualificationGate(id='release_evidence', status='PASS', evidence=[evidence('release_manifest', 'manifest')], facts=ReleaseEvidenceFacts(project='react-fastapi-base', profile='company', candidate_version=VERSION, verified_source_commit=source_commit, source_digest=source_digest, evidence_commit='3' * 40, target_base_sha='6b3d7a69b37d04cbd015c63bea17a8f859e7a7cf', readiness_matrix_sha256='6' * 64)),
        ],
    )


def test_exact_gate_enumeration_and_statuses(tmp_path):
    model = qualified(tmp_path / 'root')
    assert [gate.id for gate in model.gates] == [
        'technical_release', 'identity', 'storage', 'deployment',
        'ui_accessibility', 'performance', 'operations', 'release_evidence',
    ]
    assert all(gate.status == 'PASS' for gate in model.gates)
    assert model.derived_production_ready(expected_version=VERSION, expected_deployment_id='deployment-1', expected_root=tmp_path / 'root', expected_release_identity=repository_identity())


def test_missing_duplicate_unknown_and_illegal_gate_statuses_fail_closed(tmp_path):
    payload = qualified(tmp_path / 'root').model_dump()
    payload['gates'] = payload['gates'][:-1]
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(payload)
    payload = qualified(tmp_path / 'root').model_dump()
    payload['gates'][-1] = payload['gates'][0]
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(payload)
    payload = qualified(tmp_path / 'root').model_dump()
    payload['gates'][0]['id'] = 'unknown'
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(payload)
    payload = qualified(tmp_path / 'root').model_dump()
    payload['gates'][0]['status'] = 'NOT_APPLICABLE'
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(payload)


def test_pass_requires_evidence_and_typed_facts(tmp_path):
    payload = qualified(tmp_path / 'root').model_dump()
    payload['gates'][0]['evidence'] = []
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(payload)
    payload = qualified(tmp_path / 'root').model_dump()
    payload['gates'][0]['facts'] = None
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(payload)


def test_legacy_schema_cannot_certify_and_reports_migration(tmp_path):
    legacy = {
        'schema_version': 1,
        'deployment_id': 'deployment-1',
        'identity_topology': 'per_user_process',
        'simultaneous_identity_evidence': 'legacy-reference',
        'storage_kind': 'local_disk',
        'provider_sqlite_support_reference': 'legacy-reference',
        'all_database_clients_same_host': True,
        'persistent_root': str((tmp_path / 'root').resolve()),
        'redeploy_persistence_evidence': 'legacy-reference',
        'restore_drill_evidence': 'legacy-reference',
        'ingress_authentication_evidence': 'legacy-reference',
        'approved_by': 'legacy-operator',
        'approved_at': '2026-09-10T00:00:00Z',
    }
    with pytest.raises(ValueError, match='schema_version 1'):
        load_company_qualification(json.dumps(legacy))
    path = tmp_path / 'legacy.json'
    path.write_text(json.dumps(legacy))
    settings = Settings(environment='production', profile='company', data_root=tmp_path / 'root', allowed_origins=['https://app.example.com'], allowed_hosts=['api.example.com'], csrf_secret='s' * 40, qualification_file=path, deployment_id='deployment-1', attachment_upload_mode='disabled')
    assert any('schema_version 1' in error for error in settings.production_errors(scanner_is_noop=False))


@pytest.mark.parametrize('field,value,expected', [
    ('project', 'other-project', 'project binding'),
    ('profile', 'development', 'profile binding'),
    ('candidate_version', '1.0.0-rc.10', 'version'),
    ('deployment_id', 'other-deployment', 'different deployment'),
    ('persistent_root', '/other/root', 'different persistent root'),
    ('source_digest', '3' * 64, 'source-digest'),
])
def test_binding_mismatches_never_derive_readiness(tmp_path, field, value, expected):
    root = tmp_path / 'root'
    payload = qualified(root).model_dump()
    payload[field] = value
    model = CompanyQualification.model_validate(payload)
    errors = model.contract_errors() + model.binding_errors(expected_version=VERSION, expected_deployment_id='deployment-1', expected_root=root, expected_release_identity=repository_identity())
    assert any(expected.casefold() in error.casefold() for error in errors)
    assert not model.derived_production_ready(expected_version=VERSION, expected_deployment_id='deployment-1', expected_root=root, expected_release_identity=repository_identity())


def test_self_consistent_fake_source_identity_is_rejected_by_repository_anchor(tmp_path):
    model = qualified(tmp_path / 'root', source_commit='1' * 40, source_digest='2' * 64)
    errors = model.binding_errors(
        expected_version=VERSION,
        expected_deployment_id='deployment-1',
        expected_root=tmp_path / 'root',
        expected_release_identity=repository_identity(),
    )
    assert any('repository RC.11 release identity' in error for error in errors)
    assert not model.derived_production_ready(
        expected_version=VERSION,
        expected_deployment_id='deployment-1',
        expected_root=tmp_path / 'root',
        expected_release_identity=repository_identity(),
    )


@pytest.mark.skipif(not REPOSITORY_RELEASE_IDENTITY_PATH.is_file(), reason='generated RC.11 repository identity is not present yet')
def test_positive_fixture_uses_repository_owned_expected_identity(tmp_path):
    expected = load_repository_release_identity()
    model = qualified(tmp_path / 'root')
    assert model.verified_source_commit == expected.verified_source_commit
    assert model.source_digest == expected.source_digest
    assert model.repository_release_identity_errors(expected) == []


def test_approval_and_production_ready_are_derived(tmp_path):
    payload = qualified(tmp_path / 'root').model_dump()
    payload.pop('approved_by')
    model = CompanyQualification.model_validate(payload)
    assert not model.derived_production_ready(expected_version=VERSION, expected_deployment_id='deployment-1', expected_root=tmp_path / 'root', expected_release_identity=repository_identity())
    payload = qualified(tmp_path / 'root').model_dump()
    payload['production_ready'] = True
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(payload)


def test_secret_bearing_evidence_reference_is_rejected_without_echoing_secret():
    secret = 'super-secret-token-value'
    with pytest.raises(ValidationError) as failure:
        EvidenceReference(kind='release_manifest', locator=f'https://evidence.example/report?token={secret}', evidence_id='record-1', issuer='release-operator')
    assert secret not in str(failure.value)


def test_template_is_complete_but_not_certifying():
    path = Path(__file__).resolve().parents[2] / 'deploy/company-qualification.template.json'
    model = CompanyQualification.model_validate_json(path.read_text())
    assert not model.derived_production_ready(expected_version=VERSION, expected_deployment_id='template', expected_root=Path('/template'), expected_release_identity=repository_identity())
