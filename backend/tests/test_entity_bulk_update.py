def project(client,title,status='planned'):
    response=client.post('/api/v1/projects',json={'title':title,'summary':'','status':status,'owner':'ops'})
    assert response.status_code==201,response.text
    return response.json()

def bulk(client,entity,targets,patch,key='bulk-edit-key'):
    return client.post(f'/api/v1/entities/{entity}/bulk-update',headers={'Idempotency-Key':key},json={'targets':[{'id':row['id'],'revision':row['revision']} for row in targets],'patch':patch})

def test_generic_bulk_update_is_atomic_revision_safe_and_audited(client):
    first=project(client,'First');second=project(client,'Second')
    response=bulk(client,'projects',[first,second],{'status':'active','owner':'platform'})
    assert response.status_code==200,response.text
    assert len(response.json()['updated'])==2
    changed=[client.get(f"/api/v1/projects/{row['id']}").json() for row in (first,second)]
    assert [row['status'] for row in changed]==['active','active']
    assert [row['owner'] for row in changed]==['platform','platform']
    assert [row['revision'] for row in changed]==[2,2]
    histories=[client.get(f"/api/v1/projects/{row['id']}/history").json() for row in changed]
    assert all(history[0]['action']=='bulk_update' for history in histories)
    # Same idempotency key returns the same operation instead of double-applying.
    repeat=bulk(client,'projects',[first,second],{'status':'active','owner':'platform'})
    assert repeat.status_code==200
    assert [client.get(f"/api/v1/projects/{row['id']}").json()['revision'] for row in changed]==[2,2]

def test_bulk_update_validates_all_targets_before_writing(client):
    first=project(client,'Atomic A');second=project(client,'Atomic B')
    newer=client.put(f"/api/v1/projects/{second['id']}",json={'title':'Atomic B','summary':'','status':'active','owner':'ops','revision':second['revision']})
    assert newer.status_code==200
    response=bulk(client,'projects',[first,second],{'owner':'should-not-apply'},'stale-bulk')
    assert response.status_code==409,response.text
    assert client.get(f"/api/v1/projects/{first['id']}").json()['owner']=='ops'
    assert client.get(f"/api/v1/projects/{first['id']}").json()['revision']==1

def test_bulk_update_rejects_readonly_unknown_and_invalid_fields(client):
    risk=client.post('/api/v1/risks',json={'title':'Computed score','status':'identified','category':'process','severity':5,'occurrence':5,'detection':5,'rpn':1,'causes':{},'mitigations':{},'prevention':{}})
    assert risk.status_code==201,risk.text
    row=risk.json()
    readonly=bulk(client,'risks',[row],{'rpn':1},'readonly-bulk')
    assert readonly.status_code==422
    assert readonly.json()['error']['code']=='bulk_field_readonly'
    unknown=bulk(client,'risks',[row],{'invented':'x'},'unknown-bulk')
    assert unknown.status_code==422
    invalid=bulk(client,'risks',[row],{'severity':99},'invalid-bulk')
    assert invalid.status_code==422
    assert invalid.json()['error']['code']=='bulk_validation'

def test_bulk_update_permissions_and_archived_records(env,client):
    row=project(client,'Permission')
    viewer=env['client']('victor')
    denied=bulk(viewer,'projects',[row],{'status':'active'},'viewer-bulk')
    assert denied.status_code==403
    archived=client.post(f"/api/v1/projects/{row['id']}/lifecycle/archive",json={'revision':row['revision']}).json()
    response=bulk(client,'projects',[archived],{'owner':'nope'},'archive-bulk')
    assert response.status_code==409
    assert response.json()['error']['code']=='archived_readonly'
