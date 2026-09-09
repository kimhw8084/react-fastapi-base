import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.platform.backup import snapshot,restore,sha256
from app.platform.database import Database
from app.platform.settings import Settings
from app.platform.migrations import assert_revision
from app.profiles.company.storage_probe import probe
from app.tooling.work_items import create_work_item_direct
from app.features.work_items.schemas import WorkItemCreate
from app.main import create_app
from app.platform.storage import LocalFilesystemStorage
import app.platform.backup as backup_module


def test_backup_restore_retains_data_and_source(env,client,item,tmp_path):
    root=env['db'].root
    before={str(p.relative_to(root)):sha256(p) for p in root.rglob('*.sqlite3')}
    out=snapshot(root,tmp_path/'backup',maintenance='APP-STOPPED')
    target=restore(out,tmp_path/'restored')
    restored=Database(Settings(environment='test',data_root=target))
    assert_revision(restored);assert_revision(restored,env['tenant'])
    from app.features.work_items.models import WorkItem
    with restored.session(env['tenant']) as session:assert session.get(WorkItem,item['id']).title==item['title']
    after={str(p.relative_to(root)):sha256(p) for p in root.rglob('*.sqlite3')}
    assert before==after
    restored.close()


def test_snapshot_enumerates_attachment_references_from_staged_database(env,tmp_path,monkeypatch):
    observed=[]
    original=backup_module._attachment_references
    def observe(path):
        observed.append(path)
        return original(path)
    monkeypatch.setattr(backup_module,'_attachment_references',observe)
    snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    assert observed
    assert all(path.name=='data.sqlite3' and path.parent.parent.parent.name.startswith('.golden-snapshot-') for path in observed)


def test_object_attachment_survives_backup_restore_and_download(env,client,item,tmp_path):
    body=b'object-backed recovery proof'
    response=client.post(f"/api/v1/work-items/{item['id']}/attachments",json={'filename':'recovery.txt','content_type':'text/plain','content_base64':base64.b64encode(body).decode()})
    assert response.status_code==201,response.text
    attachment=response.json()
    from app.platform.models import Attachment
    with env['db'].session(env['tenant']) as session:
        object_key=session.get(Attachment,attachment['id']).object_key
    assert object_key
    object_path=env['db'].root/'objects'/env['tenant']/object_key
    assert object_path.read_bytes()==body
    digest=hashlib.sha256(body).hexdigest()
    out=snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    manifest=json.loads((out/'manifest.json').read_text())
    entry=next(row for row in manifest['objects'] if row['object_key']==object_key)
    assert entry['sha256']==digest and entry['size']==len(body)
    target=restore(out,tmp_path/'restored')
    restored=Database(Settings(environment='test',profile='development',data_root=target,dev_user='alice'))
    assert_revision(restored);assert_revision(restored,env['tenant'])
    assert LocalFilesystemStorage(target/'objects').get(env['tenant'],object_key)==body
    restored.close()
    app=create_app(Settings(environment='test',profile='development',data_root=target,dev_user='alice'))
    with TestClient(app) as restored_client:
        bootstrap=restored_client.get('/api/v1/bootstrap');assert bootstrap.status_code==200
        restored_client.headers.update({'X-Tenant-Id':env['tenant'],'X-CSRF-Token':bootstrap.json()['csrf_token']})
        assert restored_client.get(f"/api/v1/work-items/{item['id']}").status_code==200
        downloaded=restored_client.get(f"/api/v1/work-items/{item['id']}/attachments/{attachment['id']}")
        assert downloaded.status_code==200 and downloaded.content==body and hashlib.sha256(downloaded.content).hexdigest()==digest


def test_missing_referenced_object_rejects_snapshot(env,client,item,tmp_path):
    response=client.post(f"/api/v1/work-items/{item['id']}/attachments",json={'filename':'missing.txt','content_type':'text/plain','content_base64':base64.b64encode(b'missing').decode()})
    assert response.status_code==201
    from app.platform.models import Attachment
    with env['db'].session(env['tenant']) as session:
        object_key=session.get(Attachment,response.json()['id']).object_key
    assert object_key
    object_path=env['db'].root/'objects'/env['tenant']/object_key;object_path.unlink()
    with pytest.raises((FileNotFoundError,ValueError)):
        snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    assert not (tmp_path/'backup').exists()


def test_corrupt_or_unsafe_object_snapshot_rejects_restore_without_target(env,client,item,tmp_path):
    response=client.post(f"/api/v1/work-items/{item['id']}/attachments",json={'filename':'corrupt.txt','content_type':'text/plain','content_base64':base64.b64encode(b'corrupt').decode()})
    assert response.status_code==201
    out=snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    manifest_path=out/'manifest.json';manifest=json.loads(manifest_path.read_text());entry=manifest['objects'][0]
    object_path=out/entry['snapshot_path'];object_path.write_bytes(b'corrupted')
    with pytest.raises(ValueError):restore(out,tmp_path/'restored-corrupt')
    assert not (tmp_path/'restored-corrupt').exists()
    object_path.write_bytes(b'corrupt')
    entry['snapshot_path']='objects/../escape'
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):restore(out,tmp_path/'restored-traversal')
    assert not (tmp_path/'restored-traversal').exists()


def test_restore_symlink_object_rejects_without_target(env,client,item,tmp_path):
    response=client.post(f"/api/v1/work-items/{item['id']}/attachments",json={'filename':'restore-link.txt','content_type':'text/plain','content_base64':base64.b64encode(b'link').decode()})
    assert response.status_code==201
    out=snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    entry=json.loads((out/'manifest.json').read_text())['objects'][0]
    object_path=out/entry['snapshot_path'];object_path.unlink();object_path.symlink_to(tmp_path/'outside')
    (tmp_path/'outside').write_bytes(b'link')
    with pytest.raises(ValueError):restore(out,tmp_path/'restored-symlink')
    assert not (tmp_path/'restored-symlink').exists()
    assert object_path.is_symlink()


def test_symlink_object_is_rejected_and_snapshot_is_not_modified(env,client,item,tmp_path):
    response=client.post(f"/api/v1/work-items/{item['id']}/attachments",json={'filename':'link.txt','content_type':'text/plain','content_base64':base64.b64encode(b'link').decode()})
    assert response.status_code==201
    from app.platform.models import Attachment
    with env['db'].session(env['tenant']) as session:
        object_key=session.get(Attachment,response.json()['id']).object_key
    assert object_key
    source=env['db'].root/'objects'/env['tenant']/object_key;source.unlink();source.symlink_to(tmp_path/'outside')
    (tmp_path/'outside').write_bytes(b'link')
    with pytest.raises(ValueError):snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    assert source.is_symlink() and source.resolve()==(tmp_path/'outside').resolve()

def test_restore_corruption_rejected_without_target(env,tmp_path):
    out=snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    (out/'registry.sqlite3').write_bytes(b'corrupted')
    with pytest.raises(ValueError):restore(out,tmp_path/'restored')
    assert not (tmp_path/'restored').exists()

def test_restore_path_traversal_rejected(env,tmp_path):
    out=snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    file=out/'manifest.json';data=json.loads(file.read_text());data['databases'][0]['path']='../escape.sqlite3';file.write_text(json.dumps(data))
    with pytest.raises(ValueError):restore(out,tmp_path/'restored')
    assert not (tmp_path/'escape.sqlite3').exists()

def test_live_overwrite_refused(env,tmp_path):
    out=snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    with pytest.raises(ValueError):restore(out,env['db'].root)

def test_snapshot_requires_quiescence(env,tmp_path):
    with pytest.raises(ValueError):snapshot(env['db'].root,tmp_path/'backup',maintenance='')
    with pytest.raises(ValueError):snapshot(env['db'].root,env['db'].root/'backup',maintenance='APP-STOPPED')

def test_storage_probe_is_not_certification(tmp_path):
    result=probe(tmp_path)
    assert result['diagnostic_pass']
    assert result['production_approved'] is False
    assert list(tmp_path.iterdir())==[]

def test_direct_api_uses_membership_and_audit(env):
    db=Database(env['settings'].model_copy(update={'dev_user':'bob'}))
    row=create_work_item_direct(db,env['tenant'],WorkItemCreate(title='Trusted tooling'))
    assert row.created_by=='bob'
    from app.platform.errors import AppError
    with pytest.raises(AppError):create_work_item_direct(db,env['other'],WorkItemCreate(title='No access'))
    db.close()

def test_database_missing_fails_without_creation(tmp_path):
    db=Database(Settings(data_root=tmp_path/'missing'))
    from app.platform.errors import AppError
    with pytest.raises(AppError):db.session()
    assert not db.root.exists()

def test_database_symlink_refused(env,tmp_path):
    link=env['db'].root/'registry-link.sqlite3'
    link.symlink_to(env['db'].path())
    # A symlink in a parent is also rejected rather than followed by a tool.
    alias=tmp_path/'alias';alias.symlink_to(env['db'].root,target_is_directory=True)
    # Root resolves deliberately, while database/tenant leaf symlinks are rejected.
    tenant_path=env['db'].path(env['tenant'])
    copy=tenant_path.with_suffix('.safe');tenant_path.rename(copy);tenant_path.symlink_to(copy)
    from app.platform.errors import AppError
    with pytest.raises(AppError):env['db'].session(env['tenant'])
