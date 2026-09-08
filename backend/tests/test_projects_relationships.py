from uuid import uuid4

BASE='/api/v1/projects'

def create_project(client,title='Platform hardening'):
    response=client.post(BASE,json={'title':title,'summary':'Canonical planning record','status':'active','owner':'alice'})
    assert response.status_code==201,response.text
    return response.json()

def test_projects_are_revision_safe_and_audited(client):
    project=create_project(client)
    changed=client.put(f"{BASE}/{project['id']}",json={'title':'Platform v1','summary':'Canonical planning record','status':'active','owner':'alice','revision':1})
    assert changed.status_code==200 and changed.json()['revision']==2
    stale=client.put(f"{BASE}/{project['id']}",json={'title':'Stale','summary':'','status':'planned','owner':'','revision':1})
    assert stale.status_code==409
    history=client.get(f"{BASE}/{project['id']}/history").json()
    assert [row['action'] for row in history]==['update','create']

def test_project_relationship_uses_live_canonical_labels(client,item):
    project=create_project(client,'Project Alpha')
    link=client.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':project['id'],'target_id':item['id'],'metadata':{'role':'delivery'}})
    assert link.status_code==201,link.text
    body=link.json()
    assert body['source']['label']=='Project Alpha'
    assert body['target']['label']==item['title']
    changed=client.put(f"{BASE}/{project['id']}",json={'title':'Project Alpha Renamed','summary':'Canonical planning record','status':'active','owner':'alice','revision':1})
    assert changed.status_code==200
    related=client.get('/api/v1/relationships',params={'entity':'work_items','record_id':item['id']}).json()
    assert related[0]['source']['label']=='Project Alpha Renamed'

def test_project_membership_cardinality_prevents_two_projects_for_one_work_item(client,item):
    first=create_project(client,'First')
    second=create_project(client,'Second')
    assert client.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':first['id'],'target_id':item['id']}).status_code==201
    conflict=client.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':second['id'],'target_id':item['id']})
    assert conflict.status_code==409 and conflict.json()['error']['code']=='relationship_cardinality'

def test_relationship_lifecycle_is_revision_safe(client,item):
    project=create_project(client)
    relationship=client.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':project['id'],'target_id':item['id']}).json()
    archived=client.post(f"/api/v1/relationships/{relationship['id']}/lifecycle/archive",json={'revision':1})
    assert archived.status_code==200 and archived.json()['archived'] and archived.json()['revision']==2
    assert client.post(f"/api/v1/relationships/{relationship['id']}/lifecycle/restore",json={'revision':1}).status_code==409
    restored=client.post(f"/api/v1/relationships/{relationship['id']}/lifecycle/restore",json={'revision':2})
    assert restored.status_code==200 and restored.json()['revision']==3
    history=client.get(f"/api/v1/relationships/{relationship['id']}/history").json()
    assert [row['action'] for row in history]==['restore','archive','create']

def test_relationship_rejects_missing_target_and_viewer_write(env,client):
    project=create_project(client)
    missing=client.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':project['id'],'target_id':str(uuid4())})
    assert missing.status_code==404
    viewer=env['client']('victor')
    item=client.post('/api/v1/work-items',json={'title':'Viewer target'}).json()
    denied=viewer.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':project['id'],'target_id':item['id']})
    assert denied.status_code==403
