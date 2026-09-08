from datetime import datetime,timezone,timedelta


def test_process_measurement_spec_contract_and_equipment_link(client):
    equipment=client.post('/api/v1/equipment',json={'name':'Metrology A','kind':'appliance','status':'active','power_kw':1.2}).json()
    payload={'sample_label':'S-001','process':'CMP','metric':'Thickness','value':100.2,'unit':'nm','sampled_at':'2026-09-07T12:00:00Z','target':100,'lower_spec':99,'upper_spec':101,'lot':'LOT-7'}
    created=client.post('/api/v1/process-measurements',json=payload)
    assert created.status_code==201,created.text
    row=created.json();assert row['value']==100.2
    link=client.post('/api/v1/relationships',json={'definition_key':'measurement_equipment','source_id':row['id'],'target_id':equipment['id']})
    assert link.status_code==201,link.text
    bad=client.post('/api/v1/process-measurements',json={**payload,'sample_label':'bad','lower_spec':102,'upper_spec':101})
    assert bad.status_code==422


def test_wafer_server_owns_yield_and_rejects_bad_coordinates(client):
    payload={'wafer_id':'W01','lot_id':'L01','process_step':'Probe','status':'complete','die_rows':2,'die_cols':3,'bin_map':{'good_bins':['1'],'cells':[{'x':0,'y':0,'bin':'1'},{'x':1,'y':0,'bin':'2','defect':'scratch'},{'x':2,'y':1,'bin':'1'}]},'total_die':999,'good_die':999,'defect_count':0,'yield_percent':100}
    created=client.post('/api/v1/wafer-runs',json=payload)
    assert created.status_code==201,created.text
    row=created.json();assert row['total_die']==3 and row['good_die']==2 and row['defect_count']==1
    assert 66 < row['yield_percent'] < 67
    bad=client.post('/api/v1/wafer-runs',json={**payload,'wafer_id':'W02','bin_map':{'cells':[{'x':7,'y':0,'bin':'1'}]}})
    assert bad.status_code==422


def test_lot_route_state_duration_recipe_and_cross_links(client):
    start=datetime(2026,9,7,12,tzinfo=timezone.utc)
    equipment=client.post('/api/v1/equipment',json={'name':'Etcher 12','kind':'appliance','status':'active','power_kw':4}).json()
    recipe=client.post('/api/v1/process-recipes',json={'name':'ETCH-A','version_name':'v3','process':'Etch','status':'released','parameters':{'pressure':10},'limits':{'pressure':[9,11]}})
    assert recipe.status_code==201,recipe.text
    lot=client.post('/api/v1/manufacturing-lots',json={'lot_id':'LOT-22','product':'Product A','status':'running','current_step':'Etch','quantity':25,'started_at':start.isoformat(),'target_complete':(start+timedelta(hours=8)).isoformat(),'route':{'steps':[{'id':'etch','name':'Etch','status':'running','equipment':'Etcher 12'},{'id':'met','name':'Metrology','status':'planned'}]}})
    assert lot.status_code==201,lot.text
    state=client.post('/api/v1/equipment-states',json={'label':'Etcher 12 production','state':'production','started_at':start.isoformat(),'ended_at':(start+timedelta(minutes=95)).isoformat(),'duration_minutes':1})
    assert state.status_code==201,state.text
    assert state.json()['duration_minutes']==95
    link=client.post('/api/v1/relationships',json={'definition_key':'equipment_state_equipment','source_id':state.json()['id'],'target_id':equipment['id']})
    assert link.status_code==201,link.text
    wafer=client.post('/api/v1/wafer-runs',json={'wafer_id':'W22','lot_id':'LOT-22','process_step':'Etch','die_rows':1,'die_cols':1,'bin_map':{'good_bins':['1'],'cells':[{'x':0,'y':0,'bin':'1'}]}}).json()
    for definition,target in [('wafer_lot',lot.json()['id']),('wafer_equipment',equipment['id']),('wafer_recipe',recipe.json()['id'])]:
        linked=client.post('/api/v1/relationships',json={'definition_key':definition,'source_id':wafer['id'],'target_id':target})
        assert linked.status_code==201,linked.text


def test_semiconductor_workspace_definitions_expose_pack_projections(client):
    definitions={item['key']:item for item in client.get('/api/v1/workspaces').json()}
    assert definitions['process_measurements']['visualizations'][0]=='spc'
    assert definitions['wafer_runs']['visualizations'][0]=='wafer'
    assert definitions['manufacturing_lots']['visualizations'][0]=='traveler'
    assert definitions['equipment_states']['visualizations'][0]=='state_timeline'
    assert definitions['process_recipes']['visualizations'][0]=='recipe'
