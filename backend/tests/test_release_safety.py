import base64
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.platform.attachments import AttachmentUpload, DeterministicMalwareScanner, attach
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


def test_deterministic_scanner_rejects_eicar_and_svg_without_residue(env):
    scanner=DeterministicMalwareScanner();storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    token=base64.b64encode(scanner.EICAR_TOKEN).decode()
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as rejected:
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='eicar.txt',content_type='text/plain',content_base64=token),tenant_id=env['tenant'],storage=storage,scanner=scanner)
        assert rejected.value.code=='malware_rejected'
        with pytest.raises(AppError):
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='diagram.svg',content_type='image/svg+xml',content_base64=base64.b64encode(b'<svg/>').decode()),tenant_id=env['tenant'],storage=storage,scanner=scanner)
        session.rollback()
    assert storage._objects=={}


def test_scanner_failure_is_safe_and_does_not_persist_object(env):
    class FailingScanner:
        def scan(self,content,content_type,filename):
            raise RuntimeError('provider unavailable')
    storage=MemoryStorage();actor=Actor('alice',env['tenant'],'admin','release-test',frozenset({'read','write'}))
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(AppError) as failure:
            attach(session,actor,'work_items','not-a-real-record',AttachmentUpload(filename='notes.txt',content_type='text/plain',content_base64=base64.b64encode(b'safe').decode()),tenant_id=env['tenant'],storage=storage,scanner=FailingScanner())
        assert failure.value.status==503 and failure.value.code=='scanner_unavailable'
        session.rollback()
    assert storage._objects=={}
