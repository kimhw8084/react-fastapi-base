from datetime import datetime,timezone,timedelta
import pytest


def create_service(client,name='inventory-api'):
    response=client.post('/api/v1/software-services',json={'name':name,'status':'healthy','tier':'tier_1','owner':'platform','environment':'production','config':{'replicas':3}})
    assert response.status_code==201,response.text
    return response.json()


def test_delivery_pipeline_duration_stages_and_service_link(client):
    start=datetime(2026,9,7,12,tzinfo=timezone.utc);service=create_service(client)
    created=client.post('/api/v1/delivery-runs',json={'run_id':'deploy-101','status':'passed','environment':'production','commit_sha':'abc123','branch':'main','started_at':start.isoformat(),'completed_at':(start+timedelta(minutes=8)).isoformat(),'duration_minutes':999,'stages':{'items':[{'id':'build','name':'Build','status':'passed','duration_seconds':60},{'id':'deploy','name':'Deploy','status':'passed','duration_seconds':120}]},'artifacts':{'image':'sha256:abc'}})
    assert created.status_code==201,created.text
    row=created.json();assert row['duration_minutes']==8 and len(row['stages']['items'])==2
    link=client.post('/api/v1/relationships',json={'definition_key':'delivery_service','source_id':row['id'],'target_id':service['id']})
    assert link.status_code==201,link.text
    invalid=client.post('/api/v1/delivery-runs',json={'run_id':'bad','started_at':start.isoformat(),'completed_at':(start-timedelta(minutes=1)).isoformat()})
    assert invalid.status_code==422


def test_observability_trace_and_service_link(client):
    service=create_service(client,'payments')
    root=client.post('/api/v1/observability-events',json={'event_id':'evt-root','signal':'trace','severity':'info','timestamp':'2026-09-07T12:00:00Z','duration_ms':120,'trace_id':'trace-1','span_id':'root','operation':'POST /checkout','message':'request'})
    child=client.post('/api/v1/observability-events',json={'event_id':'evt-db','signal':'trace','severity':'warning','timestamp':'2026-09-07T12:00:00.020Z','duration_ms':40,'trace_id':'trace-1','span_id':'db','parent_span_id':'root','operation':'db.select','message':'slow query'})
    assert root.status_code==201 and child.status_code==201
    linked=client.post('/api/v1/relationships',json={'definition_key':'observability_service','source_id':root.json()['id'],'target_id':service['id']})
    assert linked.status_code==201,linked.text
    bad=client.post('/api/v1/observability-events',json={'event_id':'bad','signal':'trace','severity':'info','timestamp':'2026-09-07T12:00:00Z','duration_ms':-1})
    assert bad.status_code==422


def test_incident_command_and_cross_domain_links(client):
    start=datetime(2026,9,7,12,tzinfo=timezone.utc);service=create_service(client,'gateway')
    knowledge=client.post('/api/v1/knowledge-entries',json={'title':'Gateway recovery'}).json()
    work=client.post('/api/v1/work-items',json={'title':'Correct retry storm'}).json()
    created=client.post('/api/v1/incidents',json={'incident_number':'INC-42','title':'Gateway errors','status':'resolved','severity':'sev_1','started_at':start.isoformat(),'resolved_at':(start+timedelta(minutes=35)).isoformat(),'duration_minutes':1,'commander':'alice','impact':'Checkout failures','timeline':{'events':[{'at':'2026-09-07T12:00:00Z','kind':'detected','message':'Alert fired','actor':'monitor'},{'at':'2026-09-07T12:20:00Z','kind':'mitigation','message':'Rolled back','actor':'alice'}]},'actions':{'follow_up':'retry limits'}})
    assert created.status_code==201,created.text
    row=created.json();assert row['duration_minutes']==35
    for definition,target in [('incident_service',service['id']),('incident_knowledge',knowledge['id']),('incident_work_items',work['id'])]:
        response=client.post('/api/v1/relationships',json={'definition_key':definition,'source_id':row['id'],'target_id':target})
        assert response.status_code==201,response.text


def test_slo_server_owns_budget_burn_status_and_revert(client):
    service=create_service(client,'search')
    created=client.post('/api/v1/service-objectives',json={'name':'Availability','window_days':30,'target_percent':99.9,'current_percent':99.95,'error_budget_remaining':0,'burn_rate':99,'status':'exhausted'})
    assert created.status_code==201,created.text
    row=created.json();assert row['error_budget_remaining']==pytest.approx(50) and row['burn_rate']==pytest.approx(.5) and row['status']=='healthy'
    link=client.post('/api/v1/relationships',json={'definition_key':'slo_service','source_id':row['id'],'target_id':service['id']});assert link.status_code==201
    changed=client.put(f"/api/v1/service-objectives/{row['id']}",json={'name':'Availability','window_days':30,'target_percent':99.9,'current_percent':99.8,'error_budget_remaining':100,'burn_rate':0,'status':'healthy','notes':None,'revision':1})
    assert changed.status_code==200,changed.text
    assert changed.json()['status']=='exhausted' and changed.json()['error_budget_remaining']==0
    reverted=client.post(f"/api/v1/service-objectives/{row['id']}/revert",json={'revision':2,'target_revision':1})
    assert reverted.status_code==200,reverted.text
    assert reverted.json()['status']=='healthy' and reverted.json()['error_budget_remaining']==pytest.approx(50)


def test_software_workspace_definitions_expose_pack_projections(client):
    definitions={item['key']:item for item in client.get('/api/v1/workspaces').json()}
    assert definitions['delivery_runs']['visualizations'][0]=='pipeline'
    assert definitions['observability_events']['visualizations'][0]=='observability'
    assert definitions['incidents']['visualizations'][0]=='incident_command'
    assert definitions['service_objectives']['visualizations'][0]=='slo'
    slo_fields={field['key']:field for field in definitions['service_objectives']['fields']}
    assert slo_fields['burn_rate']['read_only'] is True and slo_fields['error_budget_remaining']['read_only'] is True and slo_fields['status']['read_only'] is True
