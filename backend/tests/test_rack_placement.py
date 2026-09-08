def create_rack(client,name='R01'):
    response=client.post('/api/v1/racks',json={'name':name,'site':'Lab'})
    assert response.status_code==201,response.text
    return response.json()

def create_equipment(client,name):
    response=client.post('/api/v1/equipment',json={'name':name})
    assert response.status_code==201,response.text
    return response.json()

def place(client,rack,equipment,start,size=1,face='front'):
    return client.post('/api/v1/relationships',json={'definition_key':'rack_equipment','source_id':rack['id'],'target_id':equipment['id'],'metadata':{'start_unit':start,'size_u':size,'face':face}})

def test_rack_placement_bounds_collision_and_revision_safe_move(client):
    rack=create_rack(client);a=create_equipment(client,'srv-a');b=create_equipment(client,'srv-b')
    first=place(client,rack,a,10,2);assert first.status_code==201,first.text
    collision=place(client,rack,b,11,2);assert collision.status_code==409;assert collision.json()['error']['code']=='placement_collision'
    out=place(client,rack,b,42,2);assert out.status_code==409;assert out.json()['error']['code']=='placement_out_of_bounds'
    rear=place(client,rack,b,10,2,'rear');assert rear.status_code==201,rear.text
    moved=client.put('/api/v1/relationships/'+first.json()['id'],json={'revision':1,'metadata':{'start_unit':20,'size_u':2,'face':'front'}})
    assert moved.status_code==200,moved.text;assert moved.json()['revision']==2;assert moved.json()['metadata']['start_unit']==20
    stale=client.put('/api/v1/relationships/'+first.json()['id'],json={'revision':1,'metadata':{'start_unit':22,'size_u':2,'face':'front'}})
    assert stale.status_code==409;assert stale.json()['error']['code']=='revision_conflict'

def test_rack_optional_engineering_constraints_are_persisted_and_validated(client):
    created=client.post('/api/v1/racks',json={'name':'R-Engineering','site':'Fab 1','rack_units':42,'power_capacity_kw':20,'pdu_a_capacity_kw':10,'pdu_b_capacity_kw':10,'weight_capacity_kg':800,'thermal_capacity_kw':18,'reserved_units':4,'reserved_power_kw':2})
    assert created.status_code==201,created.text
    assert created.json()['pdu_a_capacity_kw']==10 and created.json()['weight_capacity_kg']==800
    invalid=client.post('/api/v1/racks',json={'name':'Invalid','site':'Fab 1','rack_units':4,'reserved_units':5})
    assert invalid.status_code==422

def test_equipment_can_have_only_one_active_rack_placement(client):
    rack_a=create_rack(client,'R01');rack_b=create_rack(client,'R02');equipment=create_equipment(client,'srv-a')
    assert place(client,rack_a,equipment,1).status_code==201
    second=place(client,rack_b,equipment,1)
    assert second.status_code==409;assert second.json()['error']['code']=='relationship_cardinality'

def test_archived_placement_restore_revalidates_collision(client):
    rack=create_rack(client);a=create_equipment(client,'srv-a');b=create_equipment(client,'srv-b')
    first=place(client,rack,a,5,2).json()
    archived=client.post(f"/api/v1/relationships/{first['id']}/lifecycle/archive",json={'revision':1});assert archived.status_code==200
    second=place(client,rack,b,5,2);assert second.status_code==201
    restore=client.post(f"/api/v1/relationships/{first['id']}/lifecycle/restore",json={'revision':2})
    assert restore.status_code==409;assert restore.json()['error']['code']=='placement_collision'

def test_relationship_metadata_is_bounded(client):
    project=client.post('/api/v1/projects',json={'title':'P'}).json();item=client.post('/api/v1/work-items',json={'title':'W'}).json()
    response=client.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':project['id'],'target_id':item['id'],'metadata':{'blob':'x'*17000}})
    assert response.status_code==422;assert response.json()['error']['code']=='relationship_metadata_too_large'
