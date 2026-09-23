"""Repository-owned independent frontend/backend deployment contract.

The contract is a source-bound description of the two publishers. This module
owns only contract shape and deployment-surface validation; company identity,
storage and final qualification remain owned by the selected company adapter
and ``Settings``.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / 'contracts' / 'independent-deployment.json'
RUNTIME_KEYS = frozenset({'schemaVersion', 'apiBase', 'defaultTheme', 'titleOverride'})
THEMES = frozenset({'operations', 'clarity', 'minimal'})
LOCAL_HOSTS = frozenset({'*', 'localhost', '127.0.0.1', '::1', 'testserver'})


class DeploymentContractError(ValueError):
    """A repository deployment contract or independent surface is invalid."""


def load_contract() -> dict[str, Any]:
    try:
        document = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise DeploymentContractError('Independent deployment contract is unavailable or invalid.') from error
    validate_contract(document)
    return document


def contract_sha256() -> str:
    try:
        return hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()
    except OSError as error:
        raise DeploymentContractError('Independent deployment contract is unavailable.') from error


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DeploymentContractError(message)


def validate_contract(document: Any) -> None:
    _require(isinstance(document, dict), 'Independent deployment contract must be an object.')
    _require(document.get('schema_version') == 1, 'Independent deployment contract schema is unsupported.')
    _require(document.get('contract_id') == 'react-fastapi-base.independent-deployment', 'Independent deployment contract ID is invalid.')
    _require(document.get('status') == 'repository_supported_not_company_certified', 'Independent deployment contract status is invalid.')
    topology = document.get('topology')
    _require(isinstance(topology, dict) and topology.get('independent_publishers') is True, 'Independent publisher topology is not enabled.')
    independent = topology.get('independent_publisher', {})
    _require(
        isinstance(independent, dict)
        and independent.get('api_base_required') is True
        and independent.get('api_fallback') == '404'
        and independent.get('implicit_reverse_proxy') is False
        and independent.get('co_deployment_dependency') is False,
        'Independent publisher fallback/proxy policy is invalid.',
    )
    compatibility = document.get('api_compatibility')
    _require(
        isinstance(compatibility, dict)
        and compatibility.get('major') == 1
        and compatibility.get('frontend_compiled_revision') == 2
        and compatibility.get('backend_overlap_rule') == 'same_major_and_backend_revision_greater_than_or_equal_to_frontend_compiled_revision'
        and compatibility.get('rollout_order') == 'backend_first'
        and compatibility.get('bootstrap_failure') == 'missing_incompatible_or_older_backend_fails_closed',
        'Independent API compatibility policy is invalid.',
    )
    units = document.get('units')
    _require(isinstance(units, list) and {unit.get('id') for unit in units if isinstance(unit, dict)} == {'frontend', 'backend'}, 'Independent deployment units are incomplete.')
    frontend = next(unit for unit in units if unit.get('id') == 'frontend')
    backend = next(unit for unit in units if unit.get('id') == 'backend')
    _require(frontend.get('root') == 'frontend' and frontend.get('health') == '/healthz', 'Frontend publisher contract is invalid.')
    _require(frontend.get('build', {}).get('artifact') == 'dist', 'Frontend build artifact is invalid.')
    _require(frontend.get('start', {}).get('command') == ['node', 'server.mjs'], 'Frontend start surface is invalid.')
    runtime = frontend.get('runtime_config', {})
    _require(set(runtime.get('keys', [])) == RUNTIME_KEYS and runtime.get('api_base') == 'exact_absolute_backend_origin_for_independent_publisher', 'Frontend runtime contract is invalid.')
    _require(frontend.get('api_route_policy') == {'path_prefix': '/api/', 'behavior': '404_non_proxy'}, 'Frontend API route policy is invalid.')
    _require(backend.get('root') == 'backend' and backend.get('asgi_target') == 'app.main:app', 'Backend ASGI contract is invalid.')
    _require(backend.get('health') == '/api/v1/health' and backend.get('readiness') == '/api/v1/readiness', 'Backend health/readiness contract is invalid.')
    _require(backend.get('build', {}).get('command') == ['python', '-m', 'pip', 'install', '-r', 'requirements.lock'], 'Backend build surface is invalid.')
    _require(backend.get('start', {}).get('command') == ['python', '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '${PORT:-8000}', '--workers', '1'], 'Backend start surface is invalid.')
    evidence = document.get('evidence', {})
    _require(
        isinstance(evidence, dict)
        and evidence.get('repository_proof_requires_non_empty_api_base') is True
        and evidence.get('company_qualification') == 'BLOCKED_EXTERNAL'
        and {'candidate_head', 'executable_source_commit', 'source_digest', 'contract_sha256'} <= set(evidence.get('required_identity', [])),
        'Independent deployment evidence policy is invalid.',
    )
    serialized = json.dumps(document, sort_keys=True)
    _require('accesskey' not in serialized.casefold(), 'Independent deployment contract contains forbidden identity material.')
    _require(not re.search(r'(?<![A-Za-z0-9])[0-9a-fA-F]{40}(?![A-Za-z0-9])', serialized), 'Independent deployment contract contains a fingerprint.')


def _origin(value: str, field: str) -> tuple[str, str]:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise DeploymentContractError(f'{field} must be an explicit HTTP(S) origin.')
    parsed = urlsplit(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'', '/'}:
        raise DeploymentContractError(f'{field} must be an explicit HTTP(S) origin.')
    if value.endswith('/'):
        raise DeploymentContractError(f'{field} must not end in a slash.')
    return parsed.scheme, parsed.hostname.casefold()


def validate_independent_runtime_config(
    value: Any,
    *,
    frontend_origin: str,
    backend_origin: str,
    production: bool = False,
) -> dict[str, Any]:
    """Validate the four public fields for the independent publisher path."""
    _require(isinstance(value, dict) and set(value) == RUNTIME_KEYS, 'Runtime configuration is not the strict public four-field schema.')
    _require(value.get('schemaVersion') == 1 and value.get('defaultTheme') in THEMES and isinstance(value.get('titleOverride'), str) and len(value['titleOverride']) <= 80, 'Runtime configuration fields are invalid.')
    frontend_scheme, frontend_host = _origin(frontend_origin, 'Frontend origin')
    backend_scheme, backend_host = _origin(backend_origin, 'Backend origin')
    api_base = value.get('apiBase')
    _require(isinstance(api_base, str) and api_base, 'Independent publisher runtime apiBase must be non-empty.')
    api_scheme, api_host = _origin(api_base, 'Runtime apiBase')
    _require(api_base == backend_origin and api_scheme == backend_scheme and api_host == backend_host, 'Runtime apiBase must equal the explicit backend origin.')
    _require(frontend_scheme != 'https' or api_scheme == 'https', 'An HTTPS frontend requires an HTTPS backend origin.')
    if production:
        _require(frontend_scheme == 'https' and backend_scheme == 'https', 'Production independent publishers require HTTPS origins.')
        _require(frontend_host not in LOCAL_HOSTS and backend_host not in LOCAL_HOSTS, 'Production independent publishers reject local hosts.')
    return {key: value[key] for key in ('schemaVersion', 'apiBase', 'defaultTheme', 'titleOverride')}


def validate_public_deployment_descriptor(*, frontend_origin: str, backend_origin: str, frontend_hosts: list[str], backend_hosts: list[str], production: bool = False) -> None:
    """Validate public origin/host facts without loading company evidence."""
    frontend_scheme, frontend_host = _origin(frontend_origin, 'Frontend origin')
    backend_scheme, backend_host = _origin(backend_origin, 'Backend origin')
    _require(frontend_host in {host.casefold() for host in frontend_hosts}, 'Frontend origin host is not in the publisher host allowlist.')
    _require(backend_host in {host.casefold() for host in backend_hosts}, 'Backend origin host is not in the ASGI host allowlist.')
    _require(frontend_hosts and backend_hosts and all(isinstance(host, str) and host and '/' not in host and ':' not in host for host in [*frontend_hosts, *backend_hosts]), 'Deployment host allowlists must be explicit hostnames.')
    if production:
        _require(frontend_scheme == 'https' and backend_scheme == 'https', 'Production deployment descriptors require HTTPS origins.')
        _require(not any(host.casefold() in LOCAL_HOSTS for host in [*frontend_hosts, *backend_hosts]), 'Production deployment descriptors reject local hosts.')


def company_deployment_contract_errors(settings: Any) -> list[str]:
    """Return company-boundary errors before Settings qualification checks."""
    errors: list[str] = []
    try:
        load_contract()
    except DeploymentContractError as error:
        errors.append(str(error))
        return errors
    if settings.environment not in {'qualification', 'production'}:
        return errors
    if settings.profile != 'company':
        errors.append('Company deployment contract requires the company profile.')
    if not settings.allowed_origins or any(not origin.startswith('https://') for origin in settings.allowed_origins):
        errors.append('Company deployment contract requires explicit HTTPS frontend origins.')
    if not settings.allowed_hosts or any(host.casefold() in LOCAL_HOSTS for host in settings.allowed_hosts):
        errors.append('Company deployment contract requires explicit backend hosts.')
    if not settings.deployment_id.strip() or settings.deployment_id.casefold() == 'local':
        errors.append('Company deployment contract requires an explicit deployment identity.')
    return errors
