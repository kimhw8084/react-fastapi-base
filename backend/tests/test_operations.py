import json
from pathlib import Path
import pytest
from app.platform.backup import snapshot,restore,sha256
from app.platform.database import Database
from app.platform.settings import Settings
from app.platform.migrations import assert_revision
from app.profiles.company.storage_probe import probe
from app.tooling.work_items import create_work_item_direct
from app.features.work_items.schemas import WorkItemCreate


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

def test_restore_corruption_rejected_without_target(env,tmp_path):
    out=snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    (out/'registry.sqlite3').write_bytes(b'corrupted')
    with pytest.raises(ValueError):restore(out,tmp_path/'restored')
    assert not (tmp_path/'restored').exists()

def test_restore_path_traversal_rejected(env,tmp_path):
    out=snapshot(env['db'].root,tmp_path/'backup',maintenance='APP-STOPPED')
    file=out/'manifest.json';data=json.loads(file.read_text());data['files'][0]['path']='../escape.sqlite3';file.write_text(json.dumps(data))
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
