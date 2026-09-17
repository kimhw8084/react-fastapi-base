import base64
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.platform import settings as settings_module
from app.platform.attachments import AttachmentUpload, DeterministicMalwareScanner, NoopMalwareScanner, attach
from app.platform.errors import AppError
from app.platform.security import Actor
from app.platform.settings import (
    CompanyQualification,
    CompanyQualificationGate,
    DeploymentFacts,
    EvidenceReference,
    IdentityFacts,
    OperationsFacts,
    PerformanceFacts,
    ReleaseEvidenceFacts,
    Settings,
    StorageFacts,
    TechnicalReleaseFacts,
    UiAccessibilityFacts,
    RepositoryReleaseIdentity,
    RepositorySourceEvidence,
    load_repository_release_identity,
)
from app.platform.version import VERSION
from app.platform.storage import MemoryStorage


def qualified_production_settings(tmp_path: Path, monkeypatch, *, mode: str = 'scanner_required') -> Settings:
    root=tmp_path/'qualified-data'
    def evidence(kind: str, name: str) -> EvidenceReference:
        return EvidenceReference(kind=kind, locator=f'evidence/company/{name}.json', evidence_id=f'fixture-{name}', issuer='fixture-operator')
    try:
        expected = load_repository_release_identity()
    except ValueError:
        expected = RepositoryReleaseIdentity(
            identity_type='repository_rc11_release', project='react-fastapi-base', profile='company',
            candidate_version=VERSION, verified_source_commit='a' * 40, source_digest='b' * 64,
            source_evidence=RepositorySourceEvidence(locator='evidence/test/source-hashes.json', sha256='c' * 64),
            generated_by='scripts/generate_release_identity.py', code_ready=True,
            production_ready=False, release_status='NOT_CERTIFIED',
        )
    identity_path=tmp_path/'repository-release-identity.json';identity_path.write_text(expected.model_dump_json())
    monkeypatch.setattr(settings_module,'REPOSITORY_RELEASE_IDENTITY_PATH',identity_path)
    source_commit = expected.verified_source_commit
    source_digest = expected.source_digest
    qualification=CompanyQualification(
        candidate_version=VERSION, verified_source_commit=source_commit, source_digest=source_digest,
        deployment_id='staging-1', identity_topology='per_user_process',
        storage_kind='local_disk',
        provider_sqlite_support_reference='provider evidence reference', all_database_clients_same_host=True,
        persistent_root=str(root), approved_by='release-operator', approved_at='2026-09-09T00:00:00Z',
        gates=[
            CompanyQualificationGate(id='technical_release', status='PASS', evidence=[evidence('verification_report', 'technical')], facts=TechnicalReleaseFacts(code_ready=True, candidate_version=VERSION, verified_source_commit=source_commit, source_digest=source_digest)),
            CompanyQualificationGate(id='identity', status='PASS', evidence=[evidence('identity_proof', 'identity')], facts=IdentityFacts(identity_topology='per_user_process', simultaneous_real_user_evidence=True)),
            CompanyQualificationGate(id='storage', status='PASS', evidence=[evidence('storage_proof', 'storage')], facts=StorageFacts(storage_kind='local_disk', provider_sqlite_support_reference='provider evidence reference', all_database_clients_same_host=True, persistent_root=str(root))),
            CompanyQualificationGate(id='deployment', status='PASS', evidence=[evidence('deployment_proof', 'deployment')], facts=DeploymentFacts(deployment_id='staging-1', ingress_authentication_evidence=True, redeploy_persistence_evidence=evidence('deployment_proof', 'redeploy'), restore_drill_evidence=evidence('deployment_proof', 'restore'))),
            CompanyQualificationGate(id='ui_accessibility', status='PASS', evidence=[evidence('accessibility_report', 'accessibility')], facts=UiAccessibilityFacts(company_profile_evidence=True)),
            CompanyQualificationGate(id='performance', status='PASS', evidence=[evidence('performance_report', 'performance')], facts=PerformanceFacts(company_profile_evidence=True)),
            CompanyQualificationGate(id='operations', status='PASS', evidence=[evidence('operations_report', 'operations')], facts=OperationsFacts(company_profile_evidence=True)),
            CompanyQualificationGate(id='release_evidence', status='PASS', evidence=[evidence('release_manifest', 'manifest')], facts=ReleaseEvidenceFacts(project='react-fastapi-base', profile='company', candidate_version=VERSION, verified_source_commit=source_commit, source_digest=source_digest, evidence_commit='3' * 40, target_base_sha='6b3d7a69b37d04cbd015c63bea17a8f859e7a7cf', readiness_matrix_sha256='6' * 64)),
        ],
    )
    qualification_file=tmp_path/'qualification.json';qualification_file.write_text(qualification.model_dump_json())
    return Settings(environment='production',profile='company',data_root=root,allowed_origins=['https://app.example.com'],allowed_hosts=['api.example.com'],csrf_secret='s'*40,qualification_file=qualification_file,deployment_id='staging-1',attachment_upload_mode=mode)


def test_production_scanner_required_rejects_noop_at_startup(tmp_path,monkeypatch):
    monkeypatch.setenv('AccessKey','company.alice')
    settings=qualified_production_settings(tmp_path, monkeypatch)
    assert any('NoopMalwareScanner' in error for error in settings.production_errors(scanner_is_noop=True))
    app=create_app(settings)
    with pytest.raises(RuntimeError,match='NoopMalwareScanner'):
        with TestClient(app):
            pass


def test_production_uploads_disabled_is_safe_with_noop(tmp_path,monkeypatch):
    monkeypatch.setenv('AccessKey','company.alice')
    app=create_app(qualified_production_settings(tmp_path,monkeypatch,mode='disabled'))
    with TestClient(app,base_url='https://api.example.com') as client:
        assert client.app.state.malware_scanner is None
        assert client.get('/api/v1/health').json()['alive']


def test_disabled_upload_policy_is_enforced_by_shared_service(env,item):
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    app_client=env['client']();registry=app_client.app.state.entities
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as rejected:
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=None,upload_mode='disabled',registry=registry)
        assert rejected.value.code=='attachments_disabled'
    assert storage._objects=={}


def test_disabled_upload_policy_blocks_generic_and_legacy_routes(env,item):
    disabled=env['client']('alice',attachment_upload_mode='disabled')
    payload={'filename':'notes.txt','content_type':'text/plain','content_base64':base64.b64encode(b'safe').decode()}
    generic=disabled.post(f"/api/v1/records/work_items/{item['id']}/attachments",json=payload)
    legacy=disabled.post(f"/api/v1/work-items/{item['id']}/attachments",json=payload)
    assert generic.status_code==legacy.status_code==503
    assert generic.json()['error']['code']==legacy.json()['error']['code']=='attachments_disabled'
    from app.platform.models import Attachment
    with env['db'].session(env['tenant']) as session:
        assert session.query(Attachment).count()==0
    assert not list((env['db'].root/'objects').rglob('*'))


def test_trusted_types_uses_only_bounded_file_policy(env,item):
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    app_client=env['client']();registry=app_client.app.state.entities
    with env['db'].session(env['tenant']) as session:
        accepted=attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=None,upload_mode='trusted_types',registry=registry)
        assert accepted.size==4
        with pytest.raises(AppError,match='signature'):
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='image.png',content_type='image/png',content_base64=base64.b64encode(b'not png').decode()),tenant_id=env['tenant'],storage=storage,scanner=None,upload_mode='trusted_types',registry=registry)


@pytest.mark.parametrize('scanner',[None,NoopMalwareScanner()])
def test_scanner_required_rejects_missing_or_noop_service_scanner(env,item,scanner):
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    app_client=env['client']();registry=app_client.app.state.entities
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as rejected:
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=scanner,upload_mode='scanner_required',registry=registry)
        assert rejected.value.code=='scanner_unavailable'
    assert storage._objects=={}


def test_deterministic_scanner_rejects_eicar_and_svg_without_residue(env,item):
    scanner=DeterministicMalwareScanner();storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    app_client=env['client']();registry=app_client.app.state.entities
    token=base64.b64encode(scanner.EICAR_TOKEN).decode()
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as rejected:
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='eicar.txt',content_type='text/plain',content_base64=token),tenant_id=env['tenant'],storage=storage,scanner=scanner,upload_mode='scanner_required',registry=registry)
        assert rejected.value.code=='malware_rejected'
        with pytest.raises(AppError):
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='diagram.svg',content_type='image/svg+xml',content_base64=base64.b64encode(b'<svg/>').decode()),tenant_id=env['tenant'],storage=storage,scanner=scanner,upload_mode='scanner_required',registry=registry)
        session.rollback()
    assert storage._objects=={}


def test_scanner_failure_is_safe_and_does_not_persist_object(env,item):
    class FailingScanner:
        def scan(self,content,content_type,filename):
            raise RuntimeError('provider unavailable')
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    app_client=env['client']();registry=app_client.app.state.entities
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as failure:
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=FailingScanner(),upload_mode='scanner_required',registry=registry)
        assert failure.value.status==503 and failure.value.code=='scanner_unavailable'
        session.rollback()
    assert storage._objects=={}


def test_storage_failure_after_write_is_cleaned_up_and_does_not_persist_row(env,item):
    class PartialStorage(MemoryStorage):
        def put(self, tenant_id, key, content, content_type):
            super().put(tenant_id, key, content, content_type)
            raise RuntimeError('provider failed after write')

    storage=PartialStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    app_client=env['client']();registry=app_client.app.state.entities
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as failure:
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='partial.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=None,upload_mode='trusted_types',registry=registry)
        assert failure.value.code=='storage_unavailable'
        from app.platform.models import Attachment
        assert session.query(Attachment).count()==0
    assert storage._objects=={}


def test_attachment_storage_is_bound_to_authenticated_tenant(env,item):
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    app_client=env['client']();registry=app_client.app.state.entities
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as failure:
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='cross-tenant.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=str(uuid4()),storage=storage,scanner=None,upload_mode='trusted_types',registry=registry)
        assert failure.value.status==403 and failure.value.code=='tenant_forbidden'
    assert storage._objects=={}


def test_scanner_must_return_a_boolean_approval(env,item):
    class InvalidScanner:
        def scan(self, content, content_type, filename):
            return 'approved'

    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    app_client=env['client']();registry=app_client.app.state.entities
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as failure:
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='invalid-result.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=InvalidScanner(),upload_mode='scanner_required',registry=registry)
        assert failure.value.status==503 and failure.value.code=='scanner_unavailable'
    assert storage._objects=={}


def test_shared_attachment_service_rejects_archived_record(env,item):
    app_client=env['client']();registry=app_client.app.state.entities
    assert app_client.post(f"/api/v1/work-items/{item['id']}/lifecycle/archive",json={'revision':1}).status_code==200
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as rejected:
            attach(session,actor,'work_items',item['id'],AttachmentUpload(filename='archived.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=None,upload_mode='trusted_types',registry=registry)
        assert rejected.value.status==409 and rejected.value.code=='archived_readonly'
    assert storage._objects=={}
