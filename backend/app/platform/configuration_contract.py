"""Metadata-only configuration contract and reserved namespace checks.

The contract describes configuration ownership and policy.  It is not a second
settings model: typed values and defaults remain owned by ``Settings`` and the
frontend publisher/runtime validators.
"""
from __future__ import annotations

from functools import lru_cache
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path(__file__).resolve().parents[3] / 'deploy' / 'configuration-contract.json'
_WEBHOOK_PREFIX = 'BASE_WEBHOOK_SECRET_'
_WEBHOOK_REF = re.compile(r'^[A-Z][A-Z0-9_]{0,79}$')
_RESERVED_PREFIX = 'BASE_'


class ConfigurationContractError(ValueError):
    """Safe configuration failure containing no environment values."""


@lru_cache(maxsize=1)
def load_contract() -> dict[str, Any]:
    try:
        document = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationContractError('Configuration contract is unavailable or invalid.') from error
    if not isinstance(document, dict) or document.get('schema_version') != 1 or not isinstance(document.get('entries'), list):
        raise ConfigurationContractError('Configuration contract metadata is invalid.')
    for entry in [*document['entries'], *document.get('external_platform_exceptions', [])]:
        if not isinstance(entry, dict) or not entry.get('name') or not entry.get('classification') or not entry.get('lifecycle') or not entry.get('default_policy') or not entry.get('validation_owner'):
            raise ConfigurationContractError('Configuration contract metadata is incomplete.')
    return document


def contract_entries(surface: str | None = None) -> list[dict[str, Any]]:
    entries = load_contract()['entries']
    return [entry for entry in entries if surface is None or entry.get('surface') == surface]


def backend_environment_names() -> set[str]:
    return {str(entry['name']) for entry in contract_entries('backend_environment') if 'name_pattern' not in entry}


def frontend_publisher_names() -> set[str]:
    return {str(entry['name']) for entry in contract_entries('frontend_publisher_environment')}


def runtime_config_names() -> set[str]:
    return {str(entry['name']) for entry in contract_entries('browser_runtime')}


def tooling_environment_names() -> set[str]:
    return {str(entry['name']) for entry in contract_entries('development_test_tooling')}


def collect_webhook_secrets(environment: Mapping[str, str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, value in environment.items():
        if name.startswith(_WEBHOOK_PREFIX):
            ref = name[len(_WEBHOOK_PREFIX):]
            if _WEBHOOK_REF.fullmatch(ref):
                values[ref] = value
    return values


def validate_environment_namespace(environment: Mapping[str, str]) -> None:
    """Reject unknown/case-variant backend keys without exposing values.

    ``BASE_FRONTEND_*`` is a separate publisher namespace and is deliberately
    tolerated by a backend process because local verification may share an
    environment.  The Node publisher validates that namespace independently.
    """
    reserved = [name for name in environment if name.upper().startswith(_RESERVED_PREFIX)]
    errors: list[str] = []
    by_normalized: dict[str, list[str]] = {}
    for name in reserved:
        by_normalized.setdefault(name.upper(), []).append(name)
    for normalized, spellings in sorted(by_normalized.items()):
        if len(spellings) > 1:
            errors.append(f'Ambiguous reserved configuration keys for {normalized}.')

    backend = backend_environment_names()
    tooling = tooling_environment_names()
    for name in sorted(set(reserved)):
        normalized = name.upper()
        if normalized.startswith('BASE_FRONTEND_'):
            continue
        if normalized in backend:
            if name != normalized:
                errors.append(f'Reserved configuration key must use canonical spelling: {normalized}.')
            continue
        if normalized in tooling:
            if name != normalized:
                errors.append(f'Tooling configuration key must use canonical spelling: {normalized}.')
            continue
        if name.startswith(_WEBHOOK_PREFIX):
            ref = name[len(_WEBHOOK_PREFIX):]
            if not _WEBHOOK_REF.fullmatch(ref):
                errors.append(f'Invalid webhook secret configuration key: {name}.')
            continue
        errors.append(f'Unknown backend configuration key: {name}.')
    if errors:
        raise ConfigurationContractError(' '.join(errors))


def metadata_contains_forbidden_runtime_values(value: Any) -> bool:
    """Detect value-bearing metadata fields in the authoritative artifact."""
    forbidden = {'value', 'runtime_value', 'secret_value', 'fingerprint', 'qualification_payload'}
    if isinstance(value, dict):
        return any(str(key) in forbidden or metadata_contains_forbidden_runtime_values(item) for key, item in value.items())
    if isinstance(value, list):
        return any(metadata_contains_forbidden_runtime_values(item) for item in value)
    return False

