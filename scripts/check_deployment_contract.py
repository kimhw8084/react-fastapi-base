#!/usr/bin/env python3
"""Validate the canonical independent deployment contract and its evidence."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

from app.platform.deployment_contract import (  # noqa: E402
    CONTRACT_PATH,
    contract_sha256,
    load_contract,
    validate_contract,
    validate_independent_runtime_config,
    validate_public_deployment_descriptor,
)
from app.platform.version import API_CONTRACT_REVISION, API_MAJOR  # noqa: E402
from scripts.release_version import read_candidate_version  # noqa: E402
from scripts.source_manifest import source_provenance  # noqa: E402


EXPECTED_CHECKS = (
    'provision_disposable_data',
    'frontend_build',
    'frontend_static_health',
    'frontend_static_content',
    'frontend_api_not_proxied',
    'backend_health',
    'backend_readiness',
    'cors_allows_configured_origin',
    'cors_rejects_unconfigured_origin',
    'runtime_config_public_schema',
    'cross_origin_api_bootstrap',
    'api_compatibility_current_pair',
    'api_compatibility_incompatible_major',
    'api_compatibility_older_revision',
    'runtime_origin_rejections',
    'production_descriptor_rejections',
    'frontend_stop_does_not_proxy_backend',
    'backend_stop_does_not_serve_frontend',
    'browser_api_bootstrap',
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_repository_contract() -> dict[str, object]:
    document = load_contract()
    version = read_candidate_version(ROOT).version
    _assert(document['candidate_version'] == version, 'Independent deployment contract candidate version is stale.')
    compatibility = document['api_compatibility']
    _assert(compatibility['major'] == API_MAJOR == 1, 'Independent deployment API major drifted.')
    _assert(compatibility['frontend_compiled_revision'] == API_CONTRACT_REVISION, 'Independent deployment API revision drifted.')

    runtime_source = (ROOT / 'frontend/src/platform/api/runtime.ts').read_text(encoding='utf-8')
    _assert(all(f"'{key}'" in runtime_source for key in ('schemaVersion', 'apiBase', 'defaultTheme', 'titleOverride')), 'Frontend runtime schema source drifted.')
    publisher_source = (ROOT / 'frontend/server.mjs').read_text(encoding='utf-8')
    _assert("res.writeHead(404,headers);res.end('API is published separately.')" in publisher_source, 'Frontend publisher API non-proxy behavior is missing.')
    _assert("const TYPES" in publisher_source and "'/healthz'" in publisher_source, 'Frontend publisher health surface is missing.')
    backend_source = (ROOT / 'backend/app/main.py').read_text(encoding='utf-8')
    _assert("@app.get('/api/v1/health'" in backend_source and "@app.get('/api/v1/readiness'" in backend_source, 'Backend health/readiness surface is missing.')
    company_source = (ROOT / 'backend/app/profiles/company/deployment.py').read_text(encoding='utf-8')
    _assert('company_deployment_contract_errors' in company_source, 'Company deployment boundary does not own contract validation.')
    development_source = (ROOT / 'backend/app/profiles/development/deployment.py').read_text(encoding='utf-8')
    _assert('deployment_contract' not in development_source, 'Development deployment adapter owns company deployment semantics.')

    publisher_contract = json.loads((ROOT / 'deploy/publisher-contract.json').read_text(encoding='utf-8'))
    _assert(publisher_contract.get('canonical_contract') == 'contracts/independent-deployment.json', 'Publisher metadata does not point to the canonical contract.')
    return document


def validate_evidence(path: Path, contract: dict[str, object]) -> None:
    try:
        evidence = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise AssertionError('Independent deployment evidence is missing or invalid.') from error
    serialized = json.dumps(evidence, sort_keys=True)
    _assert('accesskey' not in serialized.casefold(), 'Independent deployment evidence contains forbidden identity material.')
    _assert(not re.search(r'(?i)(?:/users/|/private/var/|/tmp/|[A-Z]:\\)', serialized), 'Independent deployment evidence contains a private filesystem value.')
    provenance = source_provenance(ROOT)
    _assert(evidence.get('status') == 'PASS', 'Independent deployment qualification did not pass.')
    _assert(evidence.get('repository_deployment_status') == 'PASS', 'Repository deployment status is not PASS.')
    _assert(evidence.get('company_deployment_status') == 'BLOCKED_EXTERNAL', 'Company deployment status must remain external.')
    _assert(evidence.get('production_ready') is False and evidence.get('company_qualification') == 'BLOCKED_EXTERNAL', 'Independent deployment evidence overclaims qualification.')
    _assert(evidence.get('qualification_environment') == 'test' and evidence.get('qualification_profile') == 'development', 'Repository deployment proof must use the deterministic development/test profile.')
    _assert(evidence.get('candidate_version') == read_candidate_version(ROOT).version, 'Independent deployment evidence candidate version is stale.')
    _assert(evidence.get('candidate_head') == provenance['executable_source_commit'], 'Independent deployment evidence executable-source identity is stale.')
    _assert(evidence.get('executable_source_commit') == provenance['executable_source_commit'], 'Independent deployment evidence executable-source identity is stale.')
    _assert(evidence.get('source_digest') == provenance['source_digest'], 'Independent deployment evidence source digest is stale.')
    _assert(evidence.get('contract_sha256') == contract_sha256(), 'Independent deployment evidence contract hash is stale.')
    roles = evidence.get('process_roles')
    _assert(isinstance(roles, dict) and set(roles) == {'frontend', 'backend'}, 'Independent deployment process roles are incomplete.')
    frontend = roles['frontend']
    backend = roles['backend']
    _assert(frontend.get('origin') and backend.get('origin') and frontend['origin'] != backend['origin'], 'Independent deployment origins are not distinct.')
    _assert(frontend.get('port') != backend.get('port'), 'Independent deployment ports are not distinct.')
    _assert(evidence.get('frontend_api_base') == backend['origin'] and evidence['frontend_api_base'], 'Independent deployment evidence did not prove a non-empty backend apiBase.')
    checks = evidence.get('checks')
    _assert(isinstance(checks, dict) and set(checks) == set(EXPECTED_CHECKS), 'Independent deployment evidence checks are incomplete.')
    _assert(all(isinstance(row, dict) and row.get('status') == 'PASS' for row in checks.values()), 'Independent deployment evidence contains a failed check.')
    validate_independent_runtime_config(
        {'schemaVersion': 1, 'apiBase': backend['origin'], 'defaultTheme': 'operations', 'titleOverride': ''},
        frontend_origin=frontend['origin'], backend_origin=backend['origin'], production=False,
    )
    validate_public_deployment_descriptor(
        frontend_origin=frontend['origin'], backend_origin=backend['origin'],
        frontend_hosts=[frontend['host']], backend_hosts=[backend['host']], production=False,
    )
    _assert(contract['evidence']['company_qualification'] == 'BLOCKED_EXTERNAL', 'Independent deployment contract external boundary drifted.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    contract = validate_repository_contract()
    if args.evidence is not None:
        validate_evidence(args.evidence.resolve(), contract)
        print(f'Independent deployment evidence passed: {args.evidence}')
    else:
        print(f'Independent deployment contract passed: {CONTRACT_PATH.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f'Independent deployment contract check FAILED: {error}')
        raise SystemExit(1) from None
