"""Load and validate the canonical operational-reliability contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / 'contracts/operational-reliability.json'

REPOSITORY_SCENARIO_IDS = (
    'OR-STARTUP-INVALID-PROFILE',
    'OR-STARTUP-NO-DEV-FALLBACK',
    'OR-READINESS-DEPENDENCY-UNAVAILABLE',
    'OR-DATABASE-SAFE-503',
    'OR-ATTACHMENT-SCANNER-FAIL-CLOSED',
    'OR-ATTACHMENT-STORAGE-FAIL-CLOSED',
    'OR-JOB-BOUNDED-RETRY',
    'OR-JOB-HEARTBEAT',
    'OR-JOB-FENCE-RECLAIM',
    'OR-WEBHOOK-UNSAFE-DESTINATION',
    'OR-WEBHOOK-DURABLE-RETRY',
    'OR-RECOVERY-INVALID-SNAPSHOT',
    'OR-DIAGNOSTICS-SAFE-REDACTION',
)
EXTERNAL_DRILL_IDS = (
    'startup_restart',
    'dependency_unavailable_recovery',
    'database_readiness_degradation',
    'worker_crash_lease_recovery',
    'outbound_integration_failure_retry',
    'recovery_restore',
    'request_log_correlation',
)


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('utf-8')


def contract_hash(contract: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(contract)).hexdigest()


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError('Operational-reliability contract is unavailable or invalid.') from error
    if not isinstance(value, dict):
        raise ValueError('Operational-reliability contract must be an object.')
    validate_contract(value)
    return value


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get('schema_version') != 1 or contract.get('contract_id') != 'react-fastapi-base.operational-reliability' or contract.get('contract_revision') != 1:
        raise ValueError('Operational-reliability contract identity is invalid.')
    scenarios = contract.get('repository_scenarios')
    if not isinstance(scenarios, list) or tuple(row.get('id') for row in scenarios if isinstance(row, dict)) != REPOSITORY_SCENARIO_IDS:
        raise ValueError('Operational-reliability repository scenario IDs drifted or are incomplete.')
    for row in scenarios:
        if not isinstance(row, dict) or not all(isinstance(row.get(key), str) and row[key] for key in ('id', 'category', 'fault', 'expected_safe_outcome')):
            raise ValueError('Operational-reliability scenario metadata is incomplete.')
        if not isinstance(row.get('reason_codes'), list) or not row['reason_codes'] or any(not isinstance(code, str) for code in row['reason_codes']):
            raise ValueError('Operational-reliability scenario reason codes are invalid.')
    external = contract.get('external_drill_categories')
    if not isinstance(external, list) or tuple(row.get('id') for row in external if isinstance(row, dict)) != EXTERNAL_DRILL_IDS:
        raise ValueError('Operational-reliability external drill categories drifted or are incomplete.')
    if any(not isinstance(row, dict) or not isinstance(row.get('required_evidence'), str) for row in external):
        raise ValueError('Operational-reliability external drill metadata is incomplete.')
    policy = contract.get('evidence_policy')
    if not isinstance(policy, dict) or policy.get('production_ready') is not False:
        raise ValueError('Operational-reliability evidence policy must remain non-certifying.')
    forbidden = policy.get('forbidden_fields')
    if not isinstance(forbidden, list) or 'production_ready' not in forbidden or 'AccessKey' not in forbidden:
        raise ValueError('Operational-reliability forbidden evidence fields are incomplete.')
