
def create_equipment(client,name='Etcher A'):
    r=client.post('/api/v1/equipment',json={'name':name,'status':'active','kind':'appliance','serial':'EQ-001','power_kw':4.5})
    assert r.status_code==201,r.text
    return r.json()

def test_knowledge_investigation_research_are_canonical_and_revision_safe(client):
    knowledge=client.post('/api/v1/knowledge-entries',json={'title':'Vacuum recovery','content':'# Recovery\n- Isolate chamber','tags':['recovery','hardware']})
    assert knowledge.status_code==201,knowledge.text
    investigation=client.post('/api/v1/investigations',json={'title':'Vacuum drift','problem':'Pressure exceeds operating band.','priority':'high','evidence':{'trace':'P-01'}})
    assert investigation.status_code==201,investigation.text
    research=client.post('/api/v1/research',json={'title':'Pump degradation study','question':'Does pump age predict drift?','phase':'hypothesis','hypothesis':'Older pumps will show higher drift.'})
    assert research.status_code==201,research.text
    changed=client.put(f"/api/v1/knowledge-entries/{knowledge.json()['id']}",json={**{k:v for k,v in knowledge.json().items() if k in {'title','entry_type','status','criticality','owner','review_state','next_review_at','content','procedures','tags'}},'title':'Vacuum recovery v2','revision':1})
    assert changed.status_code==200 and changed.json()['revision']==2
    history=client.get(f"/api/v1/knowledge-entries/{knowledge.json()['id']}/history").json()
    assert [row['action'] for row in history]==['update','create']

def test_cross_domain_relationships_use_live_labels(client):
    equipment=create_equipment(client)
    knowledge=client.post('/api/v1/knowledge-entries',json={'title':'Chamber recovery'}).json()
    investigation=client.post('/api/v1/investigations',json={'title':'Chamber fault','problem':'Intermittent stop'}).json()
    link=client.post('/api/v1/relationships',json={'definition_key':'investigation_equipment','source_id':investigation['id'],'target_id':equipment['id']})
    assert link.status_code==201,link.text
    support=client.post('/api/v1/relationships',json={'definition_key':'investigation_knowledge','source_id':investigation['id'],'target_id':knowledge['id']})
    assert support.status_code==201,support.text
    changed=client.put(f"/api/v1/equipment/{equipment['id']}",json={'name':'Etcher A2','status':'active','kind':'appliance','serial':'EQ-001','power_kw':4.5,'notes':None,'revision':1})
    assert changed.status_code==200
    related=client.get('/api/v1/relationships',params={'entity':'investigations','record_id':investigation['id']}).json()
    labels={row['target']['label'] for row in related}
    assert 'Etcher A2' in labels and 'Chamber recovery' in labels

def test_risk_scores_are_server_owned_on_create_update_and_revert(client):
    created=client.post('/api/v1/risks',json={'title':'Pump seizure','severity':8,'occurrence':4,'detection':6,'rpn':1,'residual_severity':5,'residual_occurrence':2,'residual_detection':3,'residual_rpn':999})
    assert created.status_code==201,created.text
    row=created.json();assert row['rpn']==192 and row['residual_rpn']==30
    updated=client.put(f"/api/v1/risks/{row['id']}",json={'title':'Pump seizure','status':'mitigating','category':'process','severity':9,'occurrence':3,'detection':5,'rpn':2,'residual_severity':None,'residual_occurrence':None,'residual_detection':None,'residual_rpn':999,'effect':None,'causes':{},'mitigations':{},'prevention':{},'revision':1})
    assert updated.status_code==200,updated.text
    row2=updated.json();assert row2['rpn']==135 and row2['residual_rpn'] is None
    reverted=client.post(f"/api/v1/risks/{row['id']}/revert",json={'revision':2,'target_revision':1})
    assert reverted.status_code==200,reverted.text
    assert reverted.json()['rpn']==192 and reverted.json()['residual_rpn']==30

def test_risk_links_to_investigation_and_equipment(client):
    equipment=create_equipment(client,'Litho Track')
    investigation=client.post('/api/v1/investigations',json={'title':'Track stop','problem':'Unexpected transport halt'}).json()
    risk=client.post('/api/v1/risks',json={'title':'Transport jam','severity':7,'occurrence':5,'detection':5}).json()
    a=client.post('/api/v1/relationships',json={'definition_key':'risk_investigation','source_id':risk['id'],'target_id':investigation['id']})
    b=client.post('/api/v1/relationships',json={'definition_key':'risk_equipment','source_id':risk['id'],'target_id':equipment['id']})
    assert a.status_code==201 and b.status_code==201
    duplicate_target=client.post('/api/v1/relationships',json={'definition_key':'risk_investigation','source_id':risk['id'],'target_id':investigation['id']})
    assert duplicate_target.status_code==409

def test_knowledge_workflow_and_bulk_risk_scoring_are_server_owned(client):
    knowledge=client.post('/api/v1/knowledge-entries',json={'title':'Controlled runbook','content':'Safe text'}).json()
    submitted=client.post(f"/api/v1/knowledge-entries/{knowledge['id']}/workflow/submit_review",json={'revision':1});assert submitted.status_code==200,submitted.text
    approved=client.post(f"/api/v1/knowledge-entries/{knowledge['id']}/workflow/approve",json={'revision':2});assert approved.status_code==200,approved.text
    published=client.post(f"/api/v1/knowledge-entries/{knowledge['id']}/workflow/publish",json={'revision':3});assert published.status_code==200, published.text
    assert published.json()['status']=='published' and published.json()['review_state']=='verified'
    first=client.post('/api/v1/risks',json={'title':'Score one','severity':2,'occurrence':2,'detection':2}).json()
    second=client.post('/api/v1/risks',json={'title':'Score two','severity':3,'occurrence':3,'detection':3}).json()
    scored=client.post('/api/v1/risks/score/bulk',headers={'Idempotency-Key':'risk-score-1'},json=[{'id':first['id'],'revision':1,'score':{'severity':8,'occurrence':4,'detection':2,'residual_severity':3,'residual_occurrence':2,'residual_detection':2}},{'id':second['id'],'revision':1,'score':{'severity':5,'occurrence':4,'detection':3}}])
    assert scored.status_code==200,scored.text
    by_id={row['id']:row for row in scored.json()};assert by_id[first['id']]['rpn']==64 and by_id[first['id']]['residual_rpn']==12

def test_workspace_definitions_expose_dense_custom_projections_and_readonly_scores(client):
    definitions={item['key']:item for item in client.get('/api/v1/workspaces').json()}
    assert definitions['knowledge_entries']['visualizations'][0]=='knowledge'
    assert definitions['investigations']['visualizations'][0]=='investigation'
    assert definitions['risks']['visualizations'][0]=='risk'
    assert definitions['research']['visualizations'][0]=='research'
    risk_fields={field['key']:field for field in definitions['risks']['fields']}
    assert risk_fields['rpn']['read_only'] is True and risk_fields['residual_rpn']['read_only'] is True

def test_viewer_cannot_mutate_new_intelligence_entities(env,client):
    viewer=env['client']('victor')
    denied=viewer.post('/api/v1/knowledge-entries',json={'title':'Forbidden'})
    assert denied.status_code==403
