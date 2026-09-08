def equipment(client,name,serial):
    r=client.post('/api/v1/equipment',json={'name':name,'kind':'switch' if 'Switch' in name else 'server','status':'active','serial':serial,'power_kw':1.0,'notes':None})
    assert r.status_code==201,r.text
    return r.json()

def connection(client,a,b,source_port,target_port,**metadata):
    data={'source_port':source_port,'target_port':target_port,'cable_id':metadata.pop('cable_id','CAB'),'medium':metadata.pop('medium','fiber'),'protocol':metadata.pop('protocol','ethernet'),'status':metadata.pop('status','connected'),'length_m':metadata.pop('length_m',None),'label':metadata.pop('label',''),**metadata}
    return client.post('/api/v1/relationships',json={'definition_key':'equipment_connections','source_id':a['id'],'target_id':b['id'],'metadata':data})

def test_parallel_equipment_connections_use_ports_as_uniqueness_boundary(client):
    a=equipment(client,'Server A','A');b=equipment(client,'Switch B','B')
    first=connection(client,a,b,'eth0','Gi1/0/1');assert first.status_code==201,first.text
    second=connection(client,a,b,'eth1','Gi1/0/2',cable_id='CAB-2');assert second.status_code==201,second.text
    rows=client.get('/api/v1/relationships',params={'entity':'equipment','record_id':a['id']}).json()
    assert len([row for row in rows if row['definition_key']=='equipment_connections'])==2

def test_port_occupancy_is_case_insensitive_and_cross_directional(client):
    a=equipment(client,'Server A','A');b=equipment(client,'Switch B','B');c=equipment(client,'Server C','C')
    assert connection(client,a,b,'ETH0','Gi1/0/1').status_code==201
    conflict_local=connection(client,a,c,'eth0','eth9');assert conflict_local.status_code==409 and conflict_local.json()['error']['code']=='port_occupied'
    conflict_peer=connection(client,c,b,'eth8','gi1/0/1');assert conflict_peer.status_code==409 and conflict_peer.json()['error']['code']=='port_occupied'

def test_archive_releases_port_and_restore_revalidates_occupancy(client):
    a=equipment(client,'Server A','A');b=equipment(client,'Switch B','B');c=equipment(client,'Server C','C')
    first=connection(client,a,b,'eth0','Gi1/0/1').json()
    archived=client.post(f"/api/v1/relationships/{first['id']}/lifecycle/archive",json={'revision':1});assert archived.status_code==200
    replacement=connection(client,a,c,'eth0','eth9');assert replacement.status_code==201,replacement.text
    restore=client.post(f"/api/v1/relationships/{first['id']}/lifecycle/restore",json={'revision':2})
    assert restore.status_code==409 and restore.json()['error']['code']=='port_occupied'

def test_connection_metadata_is_validated_and_revision_safe(client):
    a=equipment(client,'Server A','A');b=equipment(client,'Switch B','B')
    missing=client.post('/api/v1/relationships',json={'definition_key':'equipment_connections','source_id':a['id'],'target_id':b['id'],'metadata':{'source_port':'eth0'}})
    assert missing.status_code==422 and missing.json()['error']['code']=='invalid_connection_metadata'
    row=connection(client,a,b,'eth0','Gi1/0/1').json()
    changed=client.put(f"/api/v1/relationships/{row['id']}",json={'revision':1,'metadata':{'source_port':'eth1','target_port':'Gi1/0/2','cable_id':'CAB-X','medium':'copper','protocol':'ethernet','status':'planned','length_m':12.5,'label':'uplink'}})
    assert changed.status_code==200,changed.text
    assert changed.json()['metadata']['source_port']=='eth1' and changed.json()['revision']==2
    stale=client.put(f"/api/v1/relationships/{row['id']}",json={'revision':1,'metadata':changed.json()['metadata']})
    assert stale.status_code==409

def test_connection_definition_exposes_parallel_port_semantics(client):
    definitions={item['key']:item for item in client.get('/api/v1/relationships/definitions').json()}
    value=definitions['equipment_connections']
    assert value['kind']=='connection' and value['allow_parallel'] is True
