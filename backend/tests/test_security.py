import os
import json
from uuid import uuid4
import pytest
from app.platform.settings import Settings,CompanyQualification
from app.profiles.company.identity import CompanyIdentity
from app.platform.errors import AppError

BASE='/api/v1/work-items'

def test_viewer_cannot_write(env):
    viewer=env['client']('victor')
    assert viewer.get(BASE).status_code==200
    assert viewer.post(BASE,json={'title':'Forbidden'}).status_code==403
    assert viewer.get(BASE+'/export.csv').status_code==403
    assert viewer.get('/api/v1/audit').status_code==403

def test_editor_cannot_restore(env,client,item):
    editor=env['client']('bob')
    assert editor.post(f"{BASE}/{item['id']}/lifecycle/archive",json={'revision':1}).status_code==200
    assert editor.post(f"{BASE}/{item['id']}/lifecycle/restore",json={'revision':2}).status_code==403

def test_tenant_access_is_server_enforced(env,client,item):
    assert client.get(BASE,headers={'X-Tenant-Id':env['other']}).status_code==403
    carol=env['client']('carol');carol.headers['X-Tenant-Id']=env['other']
    assert carol.get(f"{BASE}/{item['id']}").status_code==404
    assert carol.get(BASE).json()['total']==0

def test_unprovisioned_user_cannot_self_register(env):
    c=env['client']('unknown')
    assert c.get('/api/v1/bootstrap').json()['tenants']==[]
    assert c.get(BASE).status_code==403

@pytest.mark.parametrize('tenant',['../registry','/tmp/x',str(uuid4()).upper(),'1',''])
def test_bad_tenant_identifiers(client,tenant):
    assert client.get(BASE,headers={'X-Tenant-Id':tenant}).status_code==400

def test_csrf_required(client):
    client.headers.pop('X-CSRF-Token')
    response=client.post(BASE,json={'title':'No CSRF'})
    assert response.status_code==403 and response.json()['error']['code']=='csrf_failed'

def test_cross_user_csrf_rejected(env,client):
    alice_token=client.headers['X-CSRF-Token']
    bob=env['client']('bob')
    assert bob.post(BASE,json={'title':'Wrong token'},headers={'X-CSRF-Token':alice_token}).status_code==403

def test_cross_origin_write_rejected(client):
    assert client.post(BASE,json={'title':'No'},headers={'Origin':'https://evil.invalid'}).status_code==403

def test_development_header_cannot_impersonate(client):
    bootstrap=client.get('/api/v1/bootstrap',headers={'X-User-Id':'carol','AccessKey':'carol'})
    assert bootstrap.json()['user_id']=='alice'

def test_company_identity_only_reads_accesskey(monkeypatch):
    monkeypatch.setenv('AccessKey','company.alice')
    assert CompanyIdentity().current_user()=='company.alice'
    monkeypatch.delenv('AccessKey')
    with pytest.raises(AppError):CompanyIdentity().current_user()

def test_company_missing_identity_refuses_start(env,monkeypatch):
    monkeypatch.delenv('AccessKey',raising=False)
    with pytest.raises(AppError):env['client']('alice',profile='company')

def test_production_defaults_fail_closed():
    settings=Settings(environment='production')
    assert len(settings.production_errors())>=5
    with pytest.raises(RuntimeError):settings.assert_safe()

def test_opaque_s3_mount_cannot_be_qualified():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate({'schema_version':1,'storage_kind':'s3_fuse'})


def test_qualification_template_and_placeholder_evidence_cannot_validate():
    from pathlib import Path
    from pydantic import ValidationError
    template=json.loads(Path(__file__).resolve().parents[2].joinpath('deploy/company-qualification.template.json').read_text())
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(template)
    template.update({
        'deployment_id':'looks good',
        'identity_topology':'per_user_process',
        'simultaneous_identity_evidence':'looks good',
        'storage_kind':'local_disk',
        'provider_sqlite_support_reference':'looks good',
        'all_database_clients_same_host':True,
        'persistent_root':'relative-root',
        'redeploy_persistence_evidence':'looks good',
        'restore_drill_evidence':'looks good',
        'ingress_authentication_evidence':'looks good',
        'approved_by':'approved',
        'approved_at':'not a timestamp',
    })
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate(template)


def test_production_scanner_status_is_required_for_readiness():
    settings=Settings(environment='production')
    errors=settings.production_errors()
    assert any('scanner status' in error for error in errors)
    assert not any('scanner status' in error for error in settings.maintenance_errors())

def test_shared_process_identity_cannot_be_qualified():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CompanyQualification.model_validate({'schema_version':1,'identity_topology':'shared_process'})

def test_origin_configuration_rejects_paths():
    with pytest.raises(ValueError):Settings(allowed_origins=['https://frontend.example/path'])

def test_json_only_and_body_limit(client):
    assert client.post(BASE,content='title=Injected',headers={'Content-Type':'application/x-www-form-urlencoded'}).status_code==415
    assert client.post(BASE,content=b'x'*2_000_001,headers={'Content-Type':'application/json'}).status_code==413

def test_no_sensitive_runtime_configuration(client):
    boot=client.get('/api/v1/bootstrap').json()
    assert 'data_root' not in str(boot) and 'csrf_secret' not in str(boot)
    assert client.get('/api/v1/health').json()['alive']
    assert client.get('/api/v1/readiness').json()['ready']

def test_inactive_tenant_blocked(env,client):
    from app.platform.models import Tenant
    with env['db'].session() as session:
        tenant=session.get(Tenant,env['tenant']);tenant.active=False;session.commit()
    assert client.get(BASE).status_code==403
