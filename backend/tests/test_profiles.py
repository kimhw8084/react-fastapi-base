from __future__ import annotations

from fastapi import Request

from app.main import create_app
from app.platform.profile import CompanyProfile, ProfileRuntime
from app.platform.settings import Settings
from app.platform.database import Database
from app.platform.provision import provision
from app.platform.storage import LocalFilesystemStorage
from app.profiles.company.deployment import CompanyDeploymentAdapter
from app.profiles.company.identity import CompanyIdentity
from app.profiles.company.storage import CompanyStorageAdapter
from app.profiles.development.deployment import DevelopmentDeploymentAdapter
from app.profiles.development.identity import DevelopmentIdentity
from app.profiles.development.storage import DevelopmentStorageAdapter
from app.profiles.loader import load_profile


def _request() -> Request:
    return Request({
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'headers': [(b'x-user-id', b'impersonated'), (b'accesskey', b'impersonated')],
    })


def test_trusted_profile_selection_builds_typed_development_runtime(tmp_path):
    settings = Settings(environment='test', profile='development', data_root=tmp_path / 'data')
    profile = load_profile(settings)
    runtime = profile.build_runtime(settings)

    assert isinstance(profile, CompanyProfile)
    assert profile.key == 'development'
    assert isinstance(profile.identity, DevelopmentIdentity)
    assert isinstance(profile.storage, DevelopmentStorageAdapter)
    assert isinstance(profile.deployment, DevelopmentDeploymentAdapter)
    assert isinstance(runtime, ProfileRuntime)
    assert runtime.profile is profile
    assert runtime.database.path() == (tmp_path / 'data').resolve() / 'registry.sqlite3'
    assert isinstance(runtime.object_storage, LocalFilesystemStorage)
    runtime.database.close()


def test_company_profile_owns_company_adapters_without_exposing_profile_contract(tmp_path, monkeypatch):
    settings = Settings(environment='test', profile='company', data_root=tmp_path / 'data')
    profile = load_profile(settings)
    app = create_app(settings)

    assert profile.key == 'company'
    assert profile.require_startup_identity is True
    assert isinstance(profile.identity, CompanyIdentity)
    assert isinstance(profile.storage, CompanyStorageAdapter)
    assert isinstance(profile.deployment, CompanyDeploymentAdapter)
    assert app.state.profile is not None
    assert app.state.profile_runtime.profile is app.state.profile
    assert app.state.database is app.state.profile_runtime.database
    assert app.state.storage is app.state.profile_runtime.storage
    assert app.state.object_storage is app.state.profile_runtime.object_storage
    assert app.state.identity is app.state.profile_runtime.identity
    assert app.state.deployment is app.state.profile_runtime.deployment
    monkeypatch.setenv('AccessKey', 'company.alice')
    assert app.state.profile_runtime.identity.resolve(_request()) == 'company.alice'
    app.state.profile_runtime.database.close()


def test_identity_port_is_request_aware_but_never_browser_identity_aware(monkeypatch):
    request = _request()
    assert DevelopmentIdentity('alice').resolve(request) == 'alice'
    monkeypatch.setenv('AccessKey', 'company.alice')
    assert CompanyIdentity().resolve(request) == 'company.alice'


def test_profile_runtime_is_not_serialized_by_bootstrap(tmp_path):
    from fastapi.testclient import TestClient

    settings = Settings(environment='test', profile='development', data_root=tmp_path / 'data')
    database = Database(settings)
    provision(database, 'Profile boundary fixture', settings.dev_user)
    database.close()
    app = create_app(settings)
    with TestClient(app) as client:
        payload = client.get('/api/v1/bootstrap').json()
        assert set(payload) == {'user_id', 'profile', 'csrf_token', 'tenants', 'application', 'build_version'}
        assert 'profile_runtime' not in str(payload)
        assert 'data_root' not in str(payload)
        assert 'AccessKey' not in str(payload)


def test_openapi_error_descriptions_are_stable_across_framework_versions():
    app = create_app(Settings(environment='test', profile='development'))
    responses = app.openapi()['paths']['/api/v1/health']['get']['responses']

    assert {str(code): responses[str(code)]['description'] for code in (400, 413, 415, 422, 503)} == {
        '400': 'Bad Request',
        '413': 'Content Too Large',
        '415': 'Unsupported Media Type',
        '422': 'Unprocessable Content',
        '503': 'Service Unavailable',
    }
