#!/usr/bin/env python3
"""Build source-bound repository readiness and release evidence metadata."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_version import current_release_paths, parse_candidate_version, release_paths

RELEASE_DIR = ROOT / 'evidence/current/release'
_RELEASE_PATHS = current_release_paths(ROOT)
READINESS_PATH = _RELEASE_PATHS.readiness_matrix
MANIFEST_PATH = _RELEASE_PATHS.manifest
BINDING_PATH = _RELEASE_PATHS.evidence_binding
UIQA_MATRIX_PATH = ROOT / 'evidence/current/uiqa/ui-state-matrix-results.json'
MANDATORY_GATE_IDS = (
    'technical_release',
    'identity',
    'storage',
    'deployment',
    'ui_accessibility',
    'performance',
    'operations',
    'release_evidence',
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _commit(value: str) -> bool:
    return bool(re.fullmatch(r'[0-9a-fA-F]{40}', value))


def _digest(value: str) -> bool:
    return bool(re.fullmatch(r'[0-9a-fA-F]{64}', value))


def _code_status(results: list[dict[str, Any]]) -> tuple[bool, list[str], list[str]]:
    failures = sorted(row['name'] for row in results if row.get('required_for', 'code') == 'code' and row.get('status') == 'FAIL')
    blocked = sorted(row['name'] for row in results if row.get('required_for', 'code') == 'code' and row.get('status') == 'BLOCKED')
    return not failures and not blocked, failures, blocked


def build_readiness_matrix(*, source_commit: str, source_digest: str, version: str, results: list[dict[str, Any]], deployment_id: str | None = None, persistent_root: str | None = None) -> dict[str, Any]:
    parsed_version = parse_candidate_version(version)
    artifact_paths = release_paths(parsed_version, ROOT)
    code_ready, failures, blocked = _code_status(results)
    if failures:
        technical_status = 'FAIL'
        technical_reason = 'Repository-owned code checks failed: ' + ', '.join(failures) + '.'
    elif blocked:
        technical_status = 'BLOCKED'
        technical_reason = 'Repository-owned code checks are unavailable: ' + ', '.join(blocked) + '.'
    else:
        technical_status = 'PASS'
        technical_reason = 'Repository-owned code and release checks passed for the exact candidate.'
    release_status = 'PASS' if code_ready and _commit(source_commit) and _digest(source_digest) else 'BLOCKED'
    operations_path = ROOT / 'evidence/current/operations/qualification.json'
    release_reason = (
        'Immutable source/version/digest binding metadata and this matrix are repository-bound.'
        if release_status == 'PASS' else
        'Source-bound release evidence cannot be established until the exact code candidate is verified.'
    )
    gate_rows = [
        {'id': 'technical_release', 'status': technical_status, 'reason': technical_reason, 'evidence_state': 'repository_verification'},
        {'id': 'identity', 'status': 'BLOCKED', 'qualification_status': 'BLOCKED_EXTERNAL', 'reason': 'Authentic company per-user identity and simultaneous real-user evidence is unavailable.', 'evidence_state': 'external_unproven'},
        {'id': 'storage', 'status': 'BLOCKED', 'qualification_status': 'BLOCKED_EXTERNAL', 'reason': 'Provider-supported SQLite locking, durability, persistence and restore evidence is unavailable.', 'evidence_state': 'external_unproven'},
        {'id': 'deployment', 'status': 'BLOCKED', 'qualification_status': 'BLOCKED_EXTERNAL', 'reason': 'Company publication, ingress, restart, redeploy and recovery evidence is unavailable.', 'evidence_state': 'external_unproven'},
        {'id': 'ui_accessibility', 'status': 'BLOCKED', 'qualification_status': 'BLOCKED_EXTERNAL', 'reason': 'Local browser and axe checks do not establish applicable company/profile accessibility evidence.', 'evidence_state': 'external_unproven'},
        {'id': 'performance', 'status': 'BLOCKED', 'qualification_status': 'BLOCKED_EXTERNAL', 'reason': 'Local stress checks do not establish applicable company/profile performance evidence.', 'evidence_state': 'external_unproven'},
        {'id': 'operations', 'status': 'BLOCKED', 'qualification_status': 'BLOCKED_EXTERNAL', 'reason': 'Applicable company/profile operational readiness evidence is unavailable.', 'evidence_state': 'external_unproven'},
        {'id': 'release_evidence', 'status': release_status, 'reason': release_reason, 'evidence_state': 'repository_verification'},
    ]
    return {
        'schema_version': 1,
        'report_type': 'repository-readiness-matrix',
        'project': 'react-fastapi-base',
        'profile': 'company',
        'candidate_version': version,
        'artifact_label': parsed_version.artifact_label,
        'release_artifacts': {
            'identity': str(artifact_paths.identity.relative_to(ROOT)),
            'readiness_matrix': str(artifact_paths.readiness_matrix.relative_to(ROOT)),
            'manifest': str(artifact_paths.manifest.relative_to(ROOT)),
            'evidence_binding': str(artifact_paths.evidence_binding.relative_to(ROOT)),
        },
        'verified_source_commit': source_commit,
        'source_digest': source_digest,
        'deployment_id': deployment_id,
        'persistent_root': persistent_root,
        'mandatory_gate_ids': list(MANDATORY_GATE_IDS),
        'gates': gate_rows,
        'repository_deployment': {
            'locator': 'evidence/current/deployment/qualification.json',
            'status': 'PASS' if (ROOT / 'evidence/current/deployment/qualification.json').is_file() else 'BLOCKED',
            'qualification_status': 'REPOSITORY_ONLY',
        },
        'repository_operations': {
            'locator': str(operations_path.relative_to(ROOT)),
            'status': next((row.get('status') for row in results if row.get('name') == 'operational-reliability-qualification'), 'BLOCKED'),
            'qualification_status': 'REPOSITORY_ONLY',
            'company_operations_gate': 'BLOCKED_EXTERNAL',
        },
        'code_ready': code_ready,
        'production_ready': False,
        'release_status': 'NOT_CERTIFIED',
        'note': 'Repository evidence is not an operator-approved CompanyQualification and does not certify company infrastructure.',
    }


def write_repository_release_evidence(*, source_commit: str, source_digest: str, version: str, results: list[dict[str, Any]], verification_path: str = 'evidence/current/full-stack/verification.json', api_compatibility_base_sha: str | None = None) -> dict[str, Any]:
    parsed_version = parse_candidate_version(version)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    matrix = build_readiness_matrix(
        source_commit=source_commit,
        source_digest=source_digest,
        version=version,
        results=results,
    )
    READINESS_PATH.write_text(json.dumps(matrix, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    matrix_digest = sha256_file(READINESS_PATH)
    code_ready, _, _ = _code_status(results)
    blocking_gates = [row['id'] for row in matrix['gates'] if row['status'] != 'PASS']
    uiqa_evidence = {
        'locator': str(UIQA_MATRIX_PATH.relative_to(ROOT)),
        'sha256': sha256_file(UIQA_MATRIX_PATH) if UIQA_MATRIX_PATH.is_file() else None,
        'required_for': 'code',
    }
    performance_path = ROOT / 'evidence/current/performance/qualification.json'
    performance_evidence = {
        'locator': str(performance_path.relative_to(ROOT)),
        'sha256': sha256_file(performance_path) if performance_path.is_file() else None,
        'required_for': 'code',
    }
    reusable_path = ROOT / 'evidence/current/reuse/qualification.json'
    reusable_evidence = {
        'locator': str(reusable_path.relative_to(ROOT)),
        'sha256': sha256_file(reusable_path) if reusable_path.is_file() else None,
        'required_for': 'code',
    }
    storage_path = ROOT / 'evidence/current/storage/qualification.json'
    storage_evidence = {
        'locator': str(storage_path.relative_to(ROOT)),
        'sha256': sha256_file(storage_path) if storage_path.is_file() else None,
        'required_for': 'code',
    }
    deployment_path = ROOT / 'evidence/current/deployment/qualification.json'
    deployment_evidence = {
        'locator': str(deployment_path.relative_to(ROOT)),
        'sha256': sha256_file(deployment_path) if deployment_path.is_file() else None,
        'required_for': 'code',
    }
    operations_path = ROOT / 'evidence/current/operations/qualification.json'
    operations_evidence = {
        'locator': str(operations_path.relative_to(ROOT)),
        'sha256': sha256_file(operations_path) if operations_path.is_file() else None,
        'required_for': 'code',
        'repository_status': next((row.get('status') for row in results if row.get('name') == 'operational-reliability-qualification'), 'BLOCKED'),
        'company_operations_gate': 'BLOCKED_EXTERNAL',
    }
    manifest = {
        'schema_version': 2,
        'product': 'react-fastapi-base',
        'profile': 'company',
        'version': version,
        'artifact_label': parsed_version.artifact_label,
        'release_identity': {'locator': str(release_paths(parsed_version, ROOT).identity.relative_to(ROOT))},
        'verified_source_commit': source_commit,
        'source_digest': source_digest,
        'readiness_matrix': {'locator': str(READINESS_PATH.relative_to(ROOT)), 'sha256': matrix_digest},
        'verification': {'locator': verification_path, 'source_commit': source_commit, 'source_digest': source_digest},
        'uiqa_matrix': uiqa_evidence,
        'performance_qualification': performance_evidence,
        'reusable_platform_qualification': reusable_evidence,
        'storage_qualification': storage_evidence,
        'deployment_qualification': deployment_evidence,
        'repository_operations_qualification': operations_evidence,
        'api_compatibility_base_sha': api_compatibility_base_sha,
        'target_base_sha': api_compatibility_base_sha,
        'evidence_commit': None,
        'code_ready': code_ready,
        'production_ready': False,
        'release_status': 'NOT_CERTIFIED',
        'blocking_gates': blocking_gates,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    manifest_digest = sha256_file(MANIFEST_PATH)
    binding = {
        'schema_version': 2,
        'project': 'react-fastapi-base',
        'profile': 'company',
        'version': version,
        'artifact_label': parsed_version.artifact_label,
        'release_identity': {'locator': str(release_paths(parsed_version, ROOT).identity.relative_to(ROOT))},
        'verified_source_commit': source_commit,
        'source_digest': source_digest,
        'evidence_commit': None,
        'target_base_sha': api_compatibility_base_sha,
        'readiness_matrix': {'locator': str(READINESS_PATH.relative_to(ROOT)), 'sha256': matrix_digest},
        'manifest': {'locator': str(MANIFEST_PATH.relative_to(ROOT)), 'sha256': manifest_digest},
        'uiqa_matrix': uiqa_evidence,
        'performance_qualification': performance_evidence,
        'reusable_platform_qualification': reusable_evidence,
        'storage_qualification': storage_evidence,
        'deployment_qualification': deployment_evidence,
        'repository_operations_qualification': operations_evidence,
        'binding_status': 'PENDING_EVIDENCE_COMMIT',
        'result': 'NOT_CERTIFIED',
        'note': 'Bind evidence_commit only after this exact source evidence is committed. Accepted Head and repository merge SHA are post-acceptance/integration facts and are not BUILD evidence.',
    }
    BINDING_PATH.write_text(json.dumps(binding, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return {
        'readiness_matrix': str(READINESS_PATH.relative_to(ROOT)),
        'readiness_matrix_sha256': matrix_digest,
        'manifest': str(MANIFEST_PATH.relative_to(ROOT)),
        'evidence_binding': str(BINDING_PATH.relative_to(ROOT)),
        'matrix': matrix,
    }
