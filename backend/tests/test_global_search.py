def test_global_search_returns_records_and_scoped_saved_views(client):
    created = client.post('/api/v1/work-items', json={'title': 'Backup retention review'})
    assert created.status_code == 201, created.text
    view = client.post('/api/v1/workspaces/work_items/views', json={
        'name': 'Backup review queue', 'scope': 'personal',
        'definition': {
            'search': 'backup', 'filters': {}, 'archived': False,
            'group_by': '', 'sort': 'updated_at', 'direction': 'desc',
            'density': 'comfortable', 'visualization': 'table', 'columns': [],
        },
    })
    assert view.status_code == 201, view.text
    results = client.get('/api/v1/search', params={'q': 'backup', 'limit': 10})
    assert results.status_code == 200, results.text
    assert {row['kind'] for row in results.json()} == {'record', 'saved_view'}
    scoped = client.get('/api/v1/search', params={'q': 'type:work_items backup'})
    assert scoped.status_code == 200, scoped.text
    assert all(row['kind'] == 'record' and row['entity'] == 'work_items' for row in scoped.json())


def test_global_search_rejects_blank_queries(client):
    assert client.get('/api/v1/search', params={'q': ' '}).status_code == 422
