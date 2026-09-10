import base64
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.platform.attachments import AttachmentUpload, DeterministicMalwareScanner, NoopMalwareScanner, attach
from app.platform.errors import AppError
from app.platform.security import Actor
from app.platform.settings import CompanyQualification, Settings
from app.platform.storage import MemoryStorage


def qualified_production_settings(tmp_path: Path, *, mode: str = 'scanner_required') -> Settings:
    root=tmp_path/'qualified-data'
    qualification=CompanyQualification(
        deployment_id='staging-1', identity_topology='per_user_process',
        simultaneous_identity_evidence='operator evidence reference', storage_kind='local_disk',
        provider_sqlite_support_reference='provider evidence reference', all_database_clients_same_host=True,
        persistent_root=str(root), redeploy_persistence_evidence='operator redeploy evidence',
        restore_drill_evidence='operator restore evidence', ingress_authentication_evidence='operator ingress evidence',
        approved_by='release-operator', approved_at='2026-09-09T00:00:00Z',
    )
    qualification_file=tmp_path/'qualification.json';qualification_file.write_text(qualification.model_dump_json())
    return Settings(environment='production',profile='company',data_root=root,allowed_origins=['https://app.example.com'],allowed_hosts=['api.example.com'],csrf_secret='s'*40,qualification_file=qualification_file,deployment_id='staging-1',attachment_upload_mode=mode)


def test_production_scanner_required_rejects_noop_at_startup(tmp_path,monkeypatch):
    monkeypatch.setenv('AccessKey','company.alice')
    settings=qualified_production_settings(tmp_path)
    assert any('NoopMalwareScanner' in error for error in settings.production_errors(scanner_is_noop=True))
    app=create_app(settings)
    with pytest.raises(RuntimeError,match='NoopMalwareScanner'):
        with TestClient(app):
            pass


def test_production_uploads_disabled_is_safe_with_noop(tmp_path,monkeypatch):
    monkeypatch.setenv('AccessKey','company.alice')
    app=create_app(qualified_production_settings(tmp_path,mode='disabled'))
    with TestClient(app,base_url='https://api.example.com') as client:
        assert client.app.state.malware_scanner is None
        assert client.get('/api/v1/health').json()['alive']


def test_disabled_upload_policy_is_enforced_by_shared_service(env):
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as rejected:
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=None,upload_mode='disabled')
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


def test_trusted_types_uses_only_bounded_file_policy(env):
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    with env['db'].session(env['tenant']) as session:
        accepted=attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=None,upload_mode='trusted_types')
        assert accepted.size==4
        with pytest.raises(AppError,match='signature'):
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='image.png',content_type='image/png',content_base64=base64.b64encode(b'not png').decode()),tenant_id=env['tenant'],storage=storage,scanner=None,upload_mode='trusted_types')


@pytest.mark.parametrize('scanner',[None,NoopMalwareScanner()])
def test_scanner_required_rejects_missing_or_noop_service_scanner(env,scanner):
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as rejected:
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=scanner,upload_mode='scanner_required')
        assert rejected.value.code=='scanner_unavailable'
    assert storage._objects=={}


def test_deterministic_scanner_rejects_eicar_and_svg_without_residue(env):
    scanner=DeterministicMalwareScanner();storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    token=base64.b64encode(scanner.EICAR_TOKEN).decode()
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as rejected:
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='eicar.txt',content_type='text/plain',content_base64=token),tenant_id=env['tenant'],storage=storage,scanner=scanner,upload_mode='scanner_required')
        assert rejected.value.code=='malware_rejected'
        with pytest.raises(AppError):
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='diagram.svg',content_type='image/svg+xml',content_base64=base64.b64encode(b'<svg/>').decode()),tenant_id=env['tenant'],storage=storage,scanner=scanner,upload_mode='scanner_required')
        session.rollback()
    assert storage._objects=={}


def test_scanner_failure_is_safe_and_does_not_persist_object(env):
    class FailingScanner:
        def scan(self,content,content_type,filename):
            raise RuntimeError('provider unavailable')
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as failure:
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=FailingScanner(),upload_mode='scanner_required')
        assert failure.value.status==503 and failure.value.code=='scanner_unavailable'
        session.rollback()
    assert storage._objects=={}
