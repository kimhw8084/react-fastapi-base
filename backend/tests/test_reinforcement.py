from datetime import datetime, timezone
import json
from app.platform.security import valid_csrf
from app.platform.schemas import AuditRead
from app.platform.settings import Settings


def test_missing_environment_is_production_fail_closed():
    settings=Settings()
    assert settings.environment=='production' and settings.profile=='company'
    assert settings.production_errors()


def test_unicode_csrf_is_rejected_without_exception():
    assert not valid_csrf('secret','alice','不正なトークン')


def test_api_serializes_utc(client,item):
    assert item['created_at'].endswith('Z') or item['created_at'].endswith('+00:00')
    history=client.get(f"/api/v1/work-items/{item['id']}/history").json()
    assert history[0]['created_at'].endswith(('Z','+00:00'))


def test_safe_identity_observation_does_not_dump_environment(client):
    response=client.get('/api/v1/identity-proof').json()
    assert response['user_id']=='alice'
    assert response['instance_id']
    assert 'data_root' not in str(response) and 'secret' not in str(response)


def test_generic_saved_filter_contract(client):
    path='/api/v1/workspaces/work_items/views'
    assert client.post(path,json={'name':'Unknown filter','definition':{'filters':{'salary':'x'}}}).status_code==422
    assert client.post(path,json={'name':'Bad sort','definition':{'sort':'raw_sql'}}).status_code==422
    response=client.post(path,json={'name':'Open high','definition':{'filters':{'status':'open','priority':'high'},'sort':'title','direction':'asc'}})
    assert response.status_code==201
    assert response.json()['definition']['filters']=={'status':'open','priority':'high'}


def test_server_policy_file_controls_authorization(env,tmp_path):
    path=tmp_path/'policy.json'
    policy=json.loads(env['settings'].policy_config.read_text())
    policy['roles']['editor']=['read','views.personal']
    path.write_text(json.dumps(policy))
    editor=env['client']('bob',policy_config=path)
    assert editor.get('/api/v1/work-items').status_code==200
    assert editor.post('/api/v1/work-items',json={'title':'Denied by application policy'}).status_code==403


def test_unknown_route_uses_error_contract(client):
    response=client.get('/api/v1/missing')
    assert response.status_code==404 and response.json()['error']['code']=='http_error'


def test_advertised_sorts_match_api(client):
    definition=client.get('/api/v1/workspaces').json()[0]
    for key in definition['sort_keys']:
        assert client.get('/api/v1/work-items',params={'sort':key}).status_code==200


def test_saved_view_link_enforces_owner(env,client):
    path='/api/v1/workspaces/work_items/views'
    view=client.post(path,json={'name':'Private link','definition':{}}).json()
    assert client.get(path+'/'+view['id']).status_code==200
    assert env['client']('bob').get(path+'/'+view['id']).status_code==404


def test_two_connections_cannot_both_accept_stale_revision(env,client,item):
    from concurrent.futures import ThreadPoolExecutor
    second=env['client']('bob')
    body={'title':'Concurrent change','description':'','status':'open','priority':'normal','revision':1}
    path='/api/v1/work-items/'+item['id']
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(c.put,path,json=body) for c in (client,second)]
        codes=sorted(f.result().status_code for f in futures)
    assert codes==[200,409]
    assert client.get(path).json()['revision']==2


def test_direct_tooling_cannot_skip_production_qualification(env):
    from app.tooling.work_items import trusted_actor
    from app.platform.database import Database
    import pytest
    database=Database(env['settings'].model_copy(update={'environment':'production','profile':'company'}))
    with pytest.raises(RuntimeError,match='Production refused'):
        trusted_actor(database,env['tenant'])
    database.close()
