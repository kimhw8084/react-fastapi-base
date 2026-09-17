from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from app.main import create_app
from app.platform.configuration_contract import ConfigurationContractError, load_contract
from app.platform.settings import Settings


def sentinel(label: str) -> str:
    return 'test-secret-' + hashlib.sha256(f'CHG32:{label}'.encode()).hexdigest()


def test_authoritative_contract_is_metadata_only_and_covers_owned_surfaces():
    contract_path = Path(__file__).resolve().parents[2] / 'deploy' / 'configuration-contract.json'
    document = json.loads(contract_path.read_text())
    encoded = json.dumps(document)
    assert document['precedence'] == [
        'trusted explicit constructor or tooling override',
        'environment value',
        'declared default policy',
    ]
    assert {'backend_environment', 'frontend_publisher_environment', 'browser_runtime', 'development_test_tooling'} <= {
        entry['surface'] for entry in document['entries']
    }
    assert 'AccessKey' in {entry['name'] for entry in document['external_platform_exceptions']}
    assert not any(forbidden in encoded for forbidden in ('CHG32-' + 'SENTINEL', 'runtime_value', 'secret_value', 'qualification_payload'))
    assert not load_contract()['entries'][0].get('value')


def test_unknown_backend_namespace_fails_closed_without_echoing_value(monkeypatch):
    value = sentinel('unknown-value')
    monkeypatch.setenv('BASE_PROFIL', value)
    with pytest.raises(ConfigurationContractError) as failure:
        Settings(environment='test', profile='development')
    assert 'BASE_PROFIL' in str(failure.value)
    assert value not in str(failure.value)


def test_frontend_namespace_is_separate_when_backend_environment_is_shared(monkeypatch):
    monkeypatch.setenv('BASE_FRONTEND_HOSTS', '["frontend.example.com"]')
    settings = Settings(environment='test', profile='development')
    assert settings.profile == 'development'


def test_conflicting_case_variant_reserved_keys_fail_closed_without_values(monkeypatch):
    monkeypatch.setenv('BASE_PROFILE', 'development')
    monkeypatch.setenv('base_profile', 'company')
    with pytest.raises(ConfigurationContractError) as failure:
        Settings(environment='test', profile='development')
    assert 'BASE_PROFILE' in str(failure.value)
    assert 'development' not in str(failure.value)
    assert 'company' not in str(failure.value)


def test_environment_requiredness_is_pure_and_profile_specific(tmp_path):
    settings = Settings(environment='qualification', profile='company', data_root=tmp_path / 'root')
    errors = settings.configuration_errors()
    assert any('prerequisites file' in error for error in errors)
    assert any('CSRF_SECRET' in error for error in errors)
    assert any('HTTPS origins' in error for error in errors)
    assert any('deployment binding' in error for error in errors)

    with pytest.raises(ConfigurationContractError, match='Configuration refused'):
        settings.assert_configuration()


def test_explicit_constructor_overrides_environment_and_defaults(monkeypatch):
    monkeypatch.setenv('BASE_DEV_USER', 'from-environment')
    monkeypatch.setenv('BASE_REQUEST_LIMIT_PER_MINUTE', '321')
    explicit = Settings(environment='test', profile='development', dev_user='explicit-user')
    from_environment = Settings(environment='test', profile='development')
    monkeypatch.delenv('BASE_REQUEST_LIMIT_PER_MINUTE')
    declared_default = Settings(environment='test', profile='development')
    assert explicit.dev_user == 'explicit-user'
    assert from_environment.request_limit_per_minute == 321
    assert declared_default.request_limit_per_minute == 180


def test_pure_validation_precedes_profile_runtime_construction(monkeypatch, tmp_path):
    settings = Settings(environment='production', profile='company', data_root=tmp_path / 'root', allowed_origins=['https://frontend.example.com'], allowed_hosts=['api.example.com'])
    called = False

    def unexpected_profile(_settings):
        nonlocal called
        called = True
        raise AssertionError('profile runtime must not be constructed')

    monkeypatch.setattr('app.main.load_profile', unexpected_profile)
    with pytest.raises(ConfigurationContractError):
        create_app(settings)
    assert called is False


def test_secret_fields_are_redacted_from_settings_surfaces_and_errors(monkeypatch):
    value = sentinel('secret-value')
    monkeypatch.setenv('BASE_CSRF_SECRET', value)
    monkeypatch.setenv('BASE_WEBHOOK_SECRET_OPS_HOOK', value)
    settings = Settings(environment='test', profile='development')
    rendered = '\n'.join((repr(settings), str(settings.model_dump()), settings.model_dump_json(), str(settings.webhook_secrets)))
    assert value not in rendered
    assert '**********' in rendered

    with pytest.raises(ConfigurationContractError) as failure:
        Settings(environment='test', profile='development', csrf_secret=[value])
    assert value not in str(failure.value)


def test_contract_loader_does_not_store_test_secret_values():
    assert sentinel('secret-value') not in json.dumps(load_contract())
