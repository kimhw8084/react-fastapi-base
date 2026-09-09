from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from app.platform.models import AuditEvent
from sqlalchemy import select,func,text

BASE='/api/v1/work-items'

def update_payload(item,**changes):
    return {**{k:item[k] for k in ('title','description','status','priority','revision')},**changes}

def test_create_persist_and_history(client,item):
    read=client.get(f"{BASE}/{item['id']}")
    assert read.status_code==200
    assert read.json()['title']==item['title']
    assert read.json()['revision']==1
    history=client.get(f"{BASE}/{item['id']}/history").json()
    assert len(history)==1 and history[0]['action']=='create' and history[0]['actor']=='alice'
    assert history[0]['request_id']

@pytest.mark.parametrize('payload',[
    {'title':''},{'title':'  '},{'title':'x'*161},{'title':'a','description':'x'*10001},
    {'title':'a','status':'invalid'},{'title':'a','priority':'urgent'},
    {'title':'a','created_by':'admin'},{'title':'a','archived':True},{'title':'a','revision':99},
])
def test_invalid_create_is_rejected(client,payload):
    result=client.post(BASE,json=payload)
    assert result.status_code==422,result.text
    assert result.json()['error']['code']=='validation_failed'
    assert client.get(BASE).json()['total']==0

def test_trim_and_unicode(client):
    row=client.post(BASE,json={'title':'  회사 업무  '}).json()
    assert row['title']=='회사 업무'

def test_optimistic_conflict_preserves_new_state(client,item):
    assert client.put(f"{BASE}/{item['id']}",json=update_payload(item,title='Changed')).status_code==200
    conflict=client.put(f"{BASE}/{item['id']}",json=update_payload(item,title='Stale'))
    assert conflict.status_code==409
    assert conflict.json()['error']['details']['current']['title']=='Changed'
    assert client.get(f"{BASE}/{item['id']}").json()['title']=='Changed'
    assert len(client.get(f"{BASE}/{item['id']}/history").json())==2

def test_simultaneous_updates_allow_one_winner(env,client,item):
    second=env['client']('bob')
    def save(c,title):return c.put(f"{BASE}/{item['id']}",json=update_payload(item,title=title)).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(save,client,'Alice change');b=pool.submit(save,second,'Bob change')
        assert sorted([a.result(),b.result()])==[200,409]
    assert client.get(f"{BASE}/{item['id']}").json()['revision']==2

def test_archive_readonly_restore(client,item):
    archived=client.post(f"{BASE}/{item['id']}/lifecycle/archive",json={'revision':1})
    assert archived.status_code==200 and archived.json()['archived']
    assert client.get(BASE).json()['total']==0
    assert client.get(BASE,params={'archived':True}).json()['total']==1
    assert client.put(f"{BASE}/{item['id']}",json=update_payload(item,revision=2)).status_code==409
    restored=client.post(f"{BASE}/{item['id']}/lifecycle/restore",json={'revision':2})
    assert restored.status_code==200 and not restored.json()['archived']
    assert restored.json()['revision']==3

def test_revert_creates_new_revision(client,item):
    client.put(f"{BASE}/{item['id']}",json=update_payload(item,title='Second title'))
    result=client.post(f"{BASE}/{item['id']}/revert",json={'revision':2,'target_revision':1})
    assert result.status_code==200 and result.json()['title']==item['title'] and result.json()['revision']==3

def test_bulk_is_atomic(client,item):
    response=client.post(BASE+'/bulk',json={'action':'archive','targets':[{'id':item['id'],'revision':1},{'id':str(uuid4()),'revision':1}]},headers={'Idempotency-Key':str(uuid4())})
    assert response.status_code==404
    assert client.get(f"{BASE}/{item['id']}").json()['revision']==1
    assert len(client.get(f"{BASE}/{item['id']}/history").json())==1

def test_bulk_duplicate_target_rejected(client,item):
    target={'id':item['id'],'revision':1}
    response=client.post(BASE+'/bulk',json={'action':'archive','targets':[target,target]},headers={'Idempotency-Key':str(uuid4())})
    assert response.status_code==422

def test_bulk_success_and_idempotent_replay(client,item):
    key=str(uuid4());body={'action':'archive','targets':[{'id':item['id'],'revision':1}]}
    first=client.post(BASE+'/bulk',json=body,headers={'Idempotency-Key':key})
    second=client.post(BASE+'/bulk',json=body,headers={'Idempotency-Key':key})
    assert first.status_code==second.status_code==200
    assert first.json()==second.json()
    assert len(client.get(f"{BASE}/{item['id']}/history").json())==2

def test_create_idempotency(client):
    key=str(uuid4())
    a=client.post(BASE,json={'title':'Once'},headers={'Idempotency-Key':key})
    b=client.post(BASE,json={'title':'Once'},headers={'Idempotency-Key':key})
    c=client.post(BASE,json={'title':'Different'},headers={'Idempotency-Key':key})
    assert a.json()['id']==b.json()['id']
    assert c.status_code==409
    assert client.get(BASE).json()['total']==1

@pytest.mark.parametrize('params',[{'sort':'DROP TABLE'},{'direction':'invalid'},{'status':'bad'},{'priority':'bad'},{'limit':0},{'limit':1001},{'offset':-1}])
def test_invalid_query(client,params):assert client.get(BASE,params=params).status_code==422

def test_search_is_literal(client):
    client.post(BASE,json={'title':'100% uptime'})
    client.post(BASE,json={'title':'Ordinary task'})
    assert client.get(BASE,params={'search':'%'}).json()['total']==1
    assert client.get(BASE,params={'search':'_'}).json()['total']==0

def test_filter_and_pagination(client):
    for title in ('C','A','B'):client.post(BASE,json={'title':title,'priority':'high'})
    result=client.get(BASE,params={'sort':'title','direction':'asc','limit':1,'offset':1,'priority':'high'}).json()
    assert result['total']==3 and result['items'][0]['title']=='B'

def test_rich_query_state_is_server_owned(client):
    client.post(BASE,json={'title':'Alpha','status':'open','priority':'high'})
    client.post(BASE,json={'title':'Beta','status':'open','priority':'low'})
    client.post(BASE,json={'title':'Gamma','status':'done','priority':'high'})
    response=client.get(BASE,params={'sorts':'[{"key":"priority","direction":"asc"},{"key":"title","direction":"desc"}]','advanced_filters':'[{"key":"status","operator":"eq","value":"open"}]'})
    assert response.status_code==200
    assert [row['title'] for row in response.json()['items']]==['Alpha','Beta']

@pytest.mark.parametrize('params',[{'sorts':'not-json'},{'sorts':'[]'*9},{'advanced_filters':'[{"key":"unknown","operator":"eq","value":"x"}]'},{'advanced_filters':'[{"key":"status","operator":"wat","value":"open"}]'}])
def test_rich_query_state_rejects_unsafe_or_invalid_shapes(client,params):
    assert client.get(BASE,params=params).status_code==422

def test_audit_table_is_append_only(env,item):
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(Exception):session.execute(text('DELETE FROM audit_events'))

def test_database_constraints_work_for_direct_clients(env):
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(Exception):
            session.execute(text("INSERT INTO work_items VALUES ('x','','','bad','high',0,0,'actor','2026-09-06','2026-09-06')"))
