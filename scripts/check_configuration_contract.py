#!/usr/bin/env python3
"""Cross-check the authoritative configuration metadata against owned code."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app.platform.configuration_contract import (  # noqa: E402
    CONTRACT_PATH,
    backend_environment_names,
    contract_entries,
    frontend_publisher_names,
    load_contract,
    metadata_contains_forbidden_runtime_values,
    runtime_config_names,
    tooling_environment_names,
)
from app.platform.settings import Settings  # noqa: E402


CLASSIFICATIONS = {
    'public_runtime',
    'server_nonsecret_private',
    'secret',
    'operator_evidence_reference',
    'development_test_only',
}
ENVIRONMENTS = {'development', 'test', 'qualification', 'production'}


def _string_array(source: str, variable: str) -> list[str]:
    match = re.search(rf'{re.escape(variable)}\s*=\s*(?:(?:Object\.freeze\()\s*)?\[([^\]]*)\]', source, re.S)
    if not match:
        raise AssertionError(f'{variable} is not declared in the owned source')
    return re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))


def _example_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for line in path.read_text(encoding='utf-8').splitlines():
        candidate = line.strip()
        if candidate.startswith('#'):
            candidate = candidate[1:].strip()
        if candidate.startswith('BASE_') and '=' in candidate:
            keys.add(candidate.split('=', 1)[0].strip())
    return keys


def main() -> int:
    document = load_contract()
    if metadata_contains_forbidden_runtime_values(document):
        raise AssertionError('Configuration contract contains a runtime-value metadata field.')
    entries = [*document['entries'], *document.get('external_platform_exceptions', [])]
    names = [str(entry['name']) for entry in entries]
    if len(names) != len(set(names)):
        raise AssertionError('Configuration contract contains duplicate key names.')
    for entry in entries:
        if entry.get('classification') not in CLASSIFICATIONS:
            raise AssertionError(f"Invalid configuration classification for {entry.get('name')!r}.")
        if set(entry.get('requiredness', {})) != ENVIRONMENTS:
            raise AssertionError(f"Requiredness is incomplete for {entry.get('name')!r}.")

    expected_backend = {
        f'BASE_{field.upper()}'
        for field in Settings.model_fields
        if field != 'webhook_secrets'
    }
    if backend_environment_names() != expected_backend:
        raise AssertionError('Settings fields and backend configuration contract drifted.')
    webhook_patterns = [entry for entry in contract_entries('backend_environment') if entry.get('name_pattern')]
    if len(webhook_patterns) != 1 or webhook_patterns[0]['name'] != 'BASE_WEBHOOK_SECRET_{SECRET_REF}':
        raise AssertionError('Dynamic webhook secret coverage is missing or ambiguous.')

    runtime_source = (ROOT / 'frontend/src/platform/api/runtime.ts').read_text(encoding='utf-8')
    runtime_source_keys = _string_array(runtime_source, 'RUNTIME_CONFIG_KEYS')
    if set(runtime_source_keys) != runtime_config_names() or len(runtime_source_keys) != len(runtime_config_names()):
        raise AssertionError('RuntimeConfig source and configuration contract drifted.')
    for path in (ROOT / 'frontend/public/runtime-config.json', ROOT / 'deploy/runtime-config.example.json'):
        if set(json.loads(path.read_text(encoding='utf-8'))) != runtime_config_names():
            raise AssertionError(f'{path.relative_to(ROOT)} is not the narrow browser runtime contract.')

    publisher_source = (ROOT / 'frontend/server.mjs').read_text(encoding='utf-8')
    publisher_source_keys = _string_array(publisher_source, 'PUBLISHER_ENV_KEYS')
    if set(publisher_source_keys) != frontend_publisher_names() or len(publisher_source_keys) != len(frontend_publisher_names()):
        raise AssertionError('Node publisher source and configuration contract drifted.')
    if _example_keys(ROOT / 'deploy/backend.env.example') != expected_backend:
        raise AssertionError('deploy/backend.env.example does not cover every backend Settings key.')
    if _example_keys(ROOT / 'deploy/frontend.env.example') != frontend_publisher_names():
        raise AssertionError('deploy/frontend.env.example does not cover every publisher key.')

    publisher_contract = json.loads((ROOT / 'deploy/publisher-contract.json').read_text(encoding='utf-8'))
    if set(publisher_contract.get('publisher_environment', [])) != frontend_publisher_names():
        raise AssertionError('Publisher contract does not cover the Node publisher namespace.')
    if set(publisher_contract.get('browser_runtime_keys', [])) != runtime_config_names():
        raise AssertionError('Publisher contract does not cover the browser runtime namespace.')

    print(
        f'Configuration contract passed: {len(expected_backend)} backend keys, '
        f'{len(frontend_publisher_names())} publisher keys, {len(runtime_config_names())} browser keys, '
        f'{len(tooling_environment_names())} test-tool keys; metadata contains no runtime values.'
    )
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, json.JSONDecodeError, ValueError) as error:
        print(f'Configuration contract check FAILED: {error}')
        raise SystemExit(1) from None
