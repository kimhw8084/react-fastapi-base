from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.platform.deployment_contract import (
    CONTRACT_PATH,
    company_deployment_contract_errors,
    contract_sha256,
    load_contract,
    validate_independent_runtime_config,
    validate_public_deployment_descriptor,
)
from app.platform.settings import Settings
from app.profiles.company.deployment import CompanyDeploymentAdapter


def test_canonical_contract_defines_two_units_and_safe_external_boundary():
    contract = load_contract()
    assert {unit['id'] for unit in contract['units']} == {'frontend', 'backend'}
    assert contract['topology']['independent_publisher']['implicit_reverse_proxy'] is False
    assert contract['topology']['same_origin_ingress']['supported'] is True
    assert contract['api_compatibility']['rollout_order'] == 'backend_first'
    assert contract['evidence']['company_qualification'] == 'BLOCKED_EXTERNAL'
    assert 'accesskey' not in json.dumps(contract).casefold()
    assert len(contract_sha256()) == 64
    assert CONTRACT_PATH.is_file()


def test_independent_runtime_requires_exact_backend_origin_and_public_shape():
    good = {'schemaVersion': 1, 'apiBase': 'http://127.0.0.1:18000', 'defaultTheme': 'operations', 'titleOverride': ''}
    assert validate_independent_runtime_config(good, frontend_origin='http://127.0.0.1:14173', backend_origin='http://127.0.0.1:18000') == good
    for bad in (
        {**good, 'apiBase': ''},
        {**good, 'apiBase': 'http://127.0.0.1:18000/api/v1'},
        {**good, 'apiBase': 'https://user:password@example.test'},
        {**good, 'private': 'server'},
    ):
        with pytest.raises(ValueError):
            validate_independent_runtime_config(bad, frontend_origin='http://127.0.0.1:14173', backend_origin='http://127.0.0.1:18000')


def test_production_descriptor_rejects_http_and_local_hosts():
    with pytest.raises(ValueError):
        validate_public_deployment_descriptor(
            frontend_origin='http://frontend.example.test', backend_origin='https://backend.example.test',
            frontend_hosts=['frontend.example.test'], backend_hosts=['backend.example.test'], production=True,
        )
    with pytest.raises(ValueError):
        validate_public_deployment_descriptor(
            frontend_origin='https://localhost', backend_origin='https://backend.example.test',
            frontend_hosts=['localhost'], backend_hosts=['backend.example.test'], production=True,
        )


def test_company_adapter_owns_production_deployment_contract_validation(tmp_path: Path):
    settings = Settings(
        environment='production', profile='company', data_root=tmp_path / 'root',
        allowed_origins=['http://frontend.example.test'], allowed_hosts=['localhost'],
        deployment_id='local', csrf_secret='s' * 40,
    )
    errors = company_deployment_contract_errors(settings)
    assert any('HTTPS' in error for error in errors)
    assert any('hosts' in error for error in errors)
    assert any('identity' in error for error in errors)
    with pytest.raises(RuntimeError, match='Company deployment contract refused'):
        CompanyDeploymentAdapter().assert_safe(settings, scanner_is_noop=False)
