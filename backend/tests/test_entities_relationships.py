from app.platform.schemas import EntityDefinition


def test_entity_registry_exposes_canonical_work_items(client,item):
    response=client.get('/api/v1/entities')
    assert response.status_code==200
    entities={row['key']:row for row in response.json()}
    assert entities['work_items']['authority']=='canonical'
    assert entities['work_items']['workspace']=='work_items'
    search=client.get('/api/v1/entities/work_items/search',params={'q':'backup'})
    assert search.status_code==200
    assert search.json()[0]['id']==item['id']
    assert search.json()[0]['label']==item['title']


def test_entity_search_is_tenant_scoped(env,client,item):
    other=env['client']('carol')
    other.headers['X-Tenant-Id']=env['other']
    boot=other.get('/api/v1/bootstrap').json()
    other.headers['X-CSRF-Token']=boot['csrf_token']
    assert other.get('/api/v1/entities/work_items/search',params={'q':item['title']}).json()==[]


def test_relationship_registry_exposes_project_work_contract(client):
    response=client.get('/api/v1/relationships/definitions')
    assert response.status_code==200
    definitions={row['key']:row for row in response.json()}
    assert definitions['project_work_items']['cardinality']=='one_to_many'
    assert definitions['project_work_items']['source_entity']=='projects'
    assert definitions['project_work_items']['target_entity']=='work_items'


def test_relationship_list_validates_entity_and_record(client,item):
    assert client.get('/api/v1/relationships',params={'entity':'missing','record_id':item['id']}).status_code==404
    assert client.get('/api/v1/relationships',params={'entity':'work_items','record_id':'missing'}).status_code==404
    assert client.get('/api/v1/relationships',params={'entity':'work_items','record_id':item['id']}).json()==[]


def test_relationship_graph_lists_entity_edges(client):
    project=client.post('/api/v1/projects',json={'title':'Graph project','summary':'','status':'planned','owner':'ops'}).json()
    item=client.post('/api/v1/work-items',json={'title':'Graph item','description':'','status':'open','priority':'normal'}).json()
    created=client.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':project['id'],'target_id':item['id'],'metadata':{}})
    assert created.status_code==201,created.text
    graph=client.get('/api/v1/relationships/graph',params={'entity':'projects'})
    assert graph.status_code==200,graph.text
    edge=next(row for row in graph.json() if row['id']==created.json()['id'])
    assert edge['source']['label']=='Graph project'
    assert edge['target']['label']=='Graph item'

def test_relationship_explorers_are_bounded_and_directional(client):
    project=client.post('/api/v1/projects',json={'title':'Explorer project','summary':'','status':'planned','owner':'ops'}).json()
    item=client.post('/api/v1/work-items',json={'title':'Explorer item','description':'','status':'open','priority':'normal'}).json()
    created=client.post('/api/v1/relationships',json={'definition_key':'project_work_items','source_id':project['id'],'target_id':item['id'],'metadata':{}}).json()
    related=client.get('/api/v1/relationships/related/explore',params={'entity':'projects','record_id':project['id']})
    assert related.status_code==200 and related.json()[0]['id']==created['id']
    backlinks=client.get('/api/v1/relationships/backlinks/explore',params={'entity':'work_items','record_id':item['id']})
    assert backlinks.status_code==200 and backlinks.json()[0]['source']['id']==project['id']
    invalid=client.get('/api/v1/relationships/explore',params={'entity':'projects','record_id':project['id'],'depth':9})
    assert invalid.status_code==422
