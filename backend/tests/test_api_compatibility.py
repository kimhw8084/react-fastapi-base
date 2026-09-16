from app.platform.version import API_CONTRACT_REVISION, API_MAJOR, VERSION


def test_bootstrap_exposes_only_safe_api_contract_metadata(client):
    response = client.get('/api/v1/bootstrap')
    assert response.status_code == 200
    payload = response.json()
    assert payload['api_major'] == API_MAJOR == 1
    assert payload['api_revision'] == API_CONTRACT_REVISION == 1
    assert set(payload) == {'user_id', 'profile', 'csrf_token', 'tenants', 'application', 'build_version', 'api_major', 'api_revision'}
    assert 'AccessKey' not in response.text
    assert 'persistent_root' not in response.text


def test_openapi_publishes_contract_metadata_separately_from_application_version(client):
    info = client.app.openapi()['info']
    assert info['version'] == VERSION
    assert info['x-api-major'] == API_MAJOR
    assert info['x-api-contract-revision'] == API_CONTRACT_REVISION
    assert info['x-api-prefix'] == '/api/v1'
