#!/usr/bin/env python3
"""Publish source-bound, metadata-only CHG-32 configuration evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

from app.platform.configuration_contract import metadata_contains_forbidden_runtime_values  # noqa: E402
from app.platform.version import API_CONTRACT_REVISION, API_MAJOR, VERSION  # noqa: E402
from scripts.source_manifest import source_provenance  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-sha', required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/release/CHG-32-configuration-contract.json')
    args = parser.parse_args()
    provenance = source_provenance(ROOT)

    contract_path = ROOT / 'deploy/configuration-contract.json'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    if metadata_contains_forbidden_runtime_values(contract):
        raise ValueError('Configuration contract contains forbidden runtime-value metadata.')
    verification_path = ROOT / 'evidence/current/full-stack/verification.json'
    api_path = ROOT / 'evidence/current/full-stack/api-compatibility.json'
    verification = json.loads(verification_path.read_text(encoding='utf-8'))
    api = json.loads(api_path.read_text(encoding='utf-8'))
    if api.get('resolved_base_sha') != args.base_sha or api.get('result') != 'PASS':
        raise ValueError('Exact-base API compatibility evidence is unavailable or failed.')

    statuses = {row['name']: row['status'] for row in verification.get('results', [])}
    required_local_checks = [
        'configuration-contract', 'architecture', 'security-source', 'backend-tests',
        'frontend-typecheck', 'frontend-unit', 'static-server', 'api-compatibility',
    ]
    missing = [name for name in required_local_checks if statuses.get(name) != 'PASS']
    if missing:
        raise ValueError('Required local evidence is not PASS: ' + ', '.join(missing))

    entries = contract['entries']
    by_surface = {}
    for entry in entries:
        surface = entry['surface']
        by_surface[surface] = by_surface.get(surface, 0) + 1
    payload = {
        'schema_version': 1,
        'project': 'react-fastapi-base',
        'change': 'CHG-32',
        'version': VERSION,
        'candidate_head': provenance['checkout_commit'],
        'checkout_commit': provenance['checkout_commit'],
        'executable_source_commit': provenance['executable_source_commit'],
        'source_digest': provenance['source_digest'],
        'source_commit': provenance['executable_source_commit'],
        'base_sha': args.base_sha,
        'contract': {
            'path': 'deploy/configuration-contract.json',
            'sha256': _sha256(contract_path),
            'metadata_only': True,
            'entries_by_surface': by_surface,
            'external_platform_exceptions': [entry['name'] for entry in contract.get('external_platform_exceptions', [])],
        },
        'precedence': contract['precedence'],
        'validation': {
            'pure_before_profile_runtime': True,
            'runtime_dependent_qualification_owner': 'CompanyProfile deployment adapter and CompanyQualification flow',
            'unknown_backend_namespace': 'fail_closed',
            'frontend_publisher_namespace': 'validated_separately; server-private',
        },
        'secret_boundary': {
            'secret_fields_redacted': True,
            'sentinel_values_recorded': False,
            'public_runtime_keys_only': ['schemaVersion', 'apiBase', 'defaultTheme', 'titleOverride'],
            'qualification_or_credential_payload_recorded': False,
        },
        'api_contract_impact': {
            'observable_change': False,
            'api_major': API_MAJOR,
            'contract_revision': API_CONTRACT_REVISION,
            'base_api_major': api.get('base_api_major'),
            'base_contract_revision': api.get('base_contract_revision'),
            'breaking_changes': api.get('breaking_changes', 0),
            'compatible_changes': api.get('compatible_changes', 0),
            'compatibility_evidence': 'evidence/current/full-stack/api-compatibility.json',
        },
        'local_checks': {name: statuses[name] for name in required_local_checks},
        'external_qualification': {
            'status': 'BLOCKED_EXTERNAL',
            'production_ready': False,
            'blockers': ['company-identity', 'company-storage', 'company-deployment'],
        },
        'evidence_policy': 'No real credentials, secret values, fingerprints or qualification payloads are copied into this report.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote metadata-only CHG-32 evidence: {args.output}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f'CHG-32 evidence generation FAILED: {error}')
        raise SystemExit(1) from None
