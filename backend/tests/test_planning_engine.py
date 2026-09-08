from datetime import date

def create_task(client,title,start='2026-09-01',end='2026-09-03',**extra):
    payload={'title':title,'start_date':start,'end_date':end,**extra}
    r=client.post('/api/v1/plan-tasks',json=payload);assert r.status_code==201,r.text;return r.json()

def test_plan_dates_duration_baseline_and_milestones_are_server_validated(client):
    row=create_task(client,'Build',start='2026-09-01',end='2026-09-05',duration_days=999)
    assert row['duration_days']==5
    bad=client.post('/api/v1/plan-tasks',json={'title':'Bad','start_date':'2026-09-05','end_date':'2026-09-01'})
    assert bad.status_code==422 and bad.json()['error']['code']=='invalid_schedule'
    baseline=client.post('/api/v1/plan-tasks',json={'title':'Baseline','start_date':'2026-09-01','end_date':'2026-09-02','baseline_start':'2026-08-31'})
    assert baseline.status_code==422 and baseline.json()['error']['code']=='invalid_baseline'
    milestone=client.post('/api/v1/plan-tasks',json={'title':'Gate','start_date':'2026-09-01','end_date':'2026-09-02','milestone':True})
    assert milestone.status_code==422 and milestone.json()['error']['code']=='invalid_milestone'

def test_plan_hierarchy_and_dependency_relationships_reject_cycles(client):
    a=create_task(client,'A');b=create_task(client,'B');c=create_task(client,'C')
    assert client.post('/api/v1/relationships',json={'definition_key':'plan_task_dependencies','source_id':b['id'],'target_id':a['id']}).status_code==201
    assert client.post('/api/v1/relationships',json={'definition_key':'plan_task_dependencies','source_id':c['id'],'target_id':b['id']}).status_code==201
    cycle=client.post('/api/v1/relationships',json={'definition_key':'plan_task_dependencies','source_id':a['id'],'target_id':c['id']})
    assert cycle.status_code==409 and cycle.json()['error']['code']=='relationship_cycle'
    assert client.post('/api/v1/relationships',json={'definition_key':'plan_task_parent','source_id':a['id'],'target_id':b['id']}).status_code==201
    hierarchy_cycle=client.post('/api/v1/relationships',json={'definition_key':'plan_task_parent','source_id':b['id'],'target_id':a['id']})
    assert hierarchy_cycle.status_code==409 and hierarchy_cycle.json()['error']['code']=='relationship_cycle'

def test_plan_task_can_belong_to_only_one_project(client):
    task=create_task(client,'Scoped')
    p1=client.post('/api/v1/projects',json={'title':'P1','status':'active','summary':'','owner':'alice'}).json()
    p2=client.post('/api/v1/projects',json={'title':'P2','status':'active','summary':'','owner':'alice'}).json()
    assert client.post('/api/v1/relationships',json={'definition_key':'project_plan_tasks','source_id':p1['id'],'target_id':task['id']}).status_code==201
    conflict=client.post('/api/v1/relationships',json={'definition_key':'project_plan_tasks','source_id':p2['id'],'target_id':task['id']})
    assert conflict.status_code==409 and conflict.json()['error']['code']=='relationship_cardinality'
