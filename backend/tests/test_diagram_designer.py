
def create_diagram(client,nodes=None,edges=None,**extra):
    payload={'title':'Architecture','nodes':nodes or {},'edges':edges or {},**extra}
    r=client.post('/api/v1/diagram-documents',json=payload);assert r.status_code==201,r.text;return r.json()

def test_diagram_counts_and_graph_integrity_are_server_owned(client):
    nodes={'a':{'label':'API','type':'service','x':10,'y':20},'b':{'label':'DB','type':'database','x':300,'y':20}}
    edges={'e1':{'source':'a','target':'b','label':'SQL','type':'data'}}
    row=create_diagram(client,nodes,edges,node_count=999,edge_count=999)
    assert row['node_count']==2 and row['edge_count']==1
    bad=client.post('/api/v1/diagram-documents',json={'title':'Bad','nodes':nodes,'edges':{'x':{'source':'a','target':'missing','label':'','type':'flow'}}})
    assert bad.status_code==422 and bad.json()['error']['code']=='invalid_diagram_edge'
    self_loop=client.post('/api/v1/diagram-documents',json={'title':'Loop','nodes':{'a':nodes['a']},'edges':{'x':{'source':'a','target':'a','label':'','type':'flow'}}})
    assert self_loop.status_code==422 and self_loop.json()['error']['code']=='invalid_diagram_edge'

def test_diagram_update_and_revert_revalidate_graph_and_counts(client):
    row=create_diagram(client,{'a':{'label':'A','type':'entity','x':0,'y':0}}, {})
    update=client.put(f"/api/v1/diagram-documents/{row['id']}",json={'title':'Architecture','diagram_type':'architecture','status':'active','nodes':{'a':{'label':'A','type':'entity','x':0,'y':0},'b':{'label':'B','type':'entity','x':100,'y':0}},'edges':{'e':{'source':'a','target':'b','label':'','type':'flow'}},'viewport':{},'node_count':0,'edge_count':0,'notes':None,'revision':1})
    assert update.status_code==200,update.text
    assert update.json()['node_count']==2 and update.json()['edge_count']==1
    reverted=client.post(f"/api/v1/diagram-documents/{row['id']}/revert",json={'revision':2,'target_revision':1})
    assert reverted.status_code==200,reverted.text
    assert reverted.json()['node_count']==1 and reverted.json()['edge_count']==0

def test_diagram_rejects_unsafe_ids_coordinates_and_viewport(client):
    bad_id=client.post('/api/v1/diagram-documents',json={'title':'Bad','nodes':{'<script>':{'label':'X','type':'entity','x':0,'y':0}},'edges':{}})
    assert bad_id.status_code==422
    bad_coord=client.post('/api/v1/diagram-documents',json={'title':'Bad','nodes':{'a':{'label':'X','type':'entity','x':999999999,'y':0}},'edges':{}})
    assert bad_coord.status_code==422
    bad_zoom=client.post('/api/v1/diagram-documents',json={'title':'Bad','nodes':{},'edges':{},'viewport':{'x':0,'y':0,'zoom':10}})
    assert bad_zoom.status_code==422

def test_diagram_workspace_defaults_to_designer(client):
    definitions={item['key']:item for item in client.get('/api/v1/workspaces').json()}
    definition=definitions['diagram_documents']
    assert definition['visualizations'][0]=='designer'
    fields={field['key']:field for field in definition['fields']}
    assert fields['node_count']['read_only'] and fields['edge_count']['read_only']
