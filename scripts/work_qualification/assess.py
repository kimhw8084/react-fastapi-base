"""Deterministic evaluators for imported, minimized work-environment evidence."""
from __future__ import annotations

from datetime import datetime
import json
import hashlib
from pathlib import Path
import re
import sys
from typing import Any

from scripts.work_qualification.reasons import GATES, GATE_PHASE, PHASES, REASONS, STATUSES
from scripts.work_qualification.safety import UnsafeEvidence, assert_safe, canonical_json, safe_text_hash

DRILLS = (
    'startup_restart', 'dependency_unavailable_recovery', 'database_readiness_degradation',
    'worker_crash_lease_recovery', 'outbound_integration_failure_retry', 'recovery_restore',
    'request_log_correlation',
)
DRILL_LABELS = {
    'startup_restart': 'startup/restart',
    'dependency_unavailable_recovery': 'dependency unavailable/recovery',
    'database_readiness_degradation': 'database readiness degradation',
    'worker_crash_lease_recovery': 'worker crash/lease recovery',
    'outbound_integration_failure_retry': 'outbound integration failure/retry',
    'recovery_restore': 'recovery/restore',
    'request_log_correlation': 'request/log correlation',
}
HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX40 = re.compile(r'^[0-9a-f]{40}$')


def phase_result(status: str, codes: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError('Unsupported phase status.')
    unique = sorted(set(codes))
    if status == 'PASS' and unique:
        unique = [code for code in unique if code.endswith('_PASS') or code in {'SRC_EXACT', 'ID_PASS_PER_USER_PROCESS', 'TENANT_CREATED', 'TENANT_REUSED', 'ST_PASS', 'DEP_PASS', 'UI_PASS', 'PERF_PASS', 'CUST_NONE', 'CUST_CONFIG_ONLY', 'CUST_SUPPORTED', 'READY_FOR_OPERATOR_APPROVAL'}]
    result = {'status': status, 'reason_codes': unique, **(extra or {})}
    if 'ATTENTION_UNKNOWN' in unique:
        result.setdefault('unknown_values_retained', False)
        result.setdefault('unknown_metadata', {'observation_shape': 'unsupported_or_missing', 'raw_value_retained': False})
    return result


def _strict_document(path: Path, expected_keys: set[str], schema_version: int = 1) -> dict[str, Any] | None:
    try:
        if path.stat().st_size > 256_000:
            return None
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict) or set(value) != expected_keys or value.get('schema_version') != schema_version:
        return None
    try:
        assert_safe(value)
    except UnsafeEvidence:
        return None
    return value


def _timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.tzinfo is not None
    except ValueError:
        return False


def _hex(value: Any, pattern: re.Pattern[str] = HEX64) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _reference_inventory(directory: Path) -> tuple[list[tuple[str, str]], bool]:
    """Accept digest-only references; raw provider documents never belong in a run."""
    accepted: list[tuple[str, str]] = []
    invalid = False
    try:
        entries = sorted(directory.iterdir())
    except OSError:
        return accepted, False
    for item in entries:
        if not item.is_file():
            invalid = True
            continue
        if not re.fullmatch(r'evidence-[a-z0-9_-]{1,40}\.sha256', item.name):
            invalid = True
            continue
        try:
            content = item.read_text(encoding='ascii').strip()
        except (OSError, UnicodeError):
            invalid = True
            continue
        if not _hex(content):
            invalid = True
            continue
        accepted.append((item.name, content))
    return accepted, invalid


def load_identity_probes(directory: Path) -> list[dict[str, Any]] | None:
    records = []
    for label in ('A1', 'B1', 'A2', 'B2', 'A3', 'B3'):
        path = directory / f'identity-{label}.json'
        expected = {
            'schema_version', 'label', 'captured_at', 'frontend_origin_hash', 'api_base_hash',
            'http', 'user_hash', 'instance_hash', 'deployment_hash', 'profile',
            'identity_source', 'build_version', 'api_major', 'api_revision',
            'tenant_hash', 'role', 'permissions',
        }
        record = _strict_document(path, expected)
        if record is None:
            return None
        if record.get('label') != label or not _timestamp(record.get('captured_at')):
            return None
        if any(not _hex(record.get(key)) for key in ('frontend_origin_hash', 'api_base_hash', 'user_hash', 'instance_hash', 'deployment_hash', 'tenant_hash')):
            return None
        if record.get('http') != {'runtime_config': 200, 'bootstrap': 200, 'identity_proof': 200}:
            return None
        if record.get('profile') not in {'company', 'development'} or record.get('identity_source') not in {'process_environment', 'explicit_development_fixture'}:
            return None
        if not isinstance(record.get('build_version'), str):
            return None
        try:
            from scripts.release_version import parse_candidate_version
            parse_candidate_version(record['build_version'])
        except ValueError:
            return None
        if any(not isinstance(record.get(key), int) or isinstance(record.get(key), bool) for key in ('api_major', 'api_revision')):
            return None
        if not isinstance(record.get('role'), str) or record.get('role') not in {'admin', 'editor', 'viewer'}:
            return None
        if not isinstance(record.get('permissions'), list) or any(not isinstance(item, str) or item not in {'admin', 'read', 'write', 'comment', 'configure', 'delete', 'export', 'import', 'restore', 'views.personal', 'views.team'} for item in record['permissions']):
            return None
        records.append(record)
    return records


def assess_identity(directory: Path, *, expected_api_major: int, expected_api_revision: int, expected_binding: dict[str, Any] | None = None) -> dict[str, Any]:
    records = load_identity_probes(directory)
    codes: list[str] = []
    if records is None:
        unknown = any((directory / f'identity-{label}.json').exists() for label in ('A1', 'B1', 'A2', 'B2', 'A3', 'B3'))
        return phase_result('BLOCKED', ['ID_MISSING', *(['ATTENTION_UNKNOWN'] if unknown else [])], {'observation_count': 0, 'provider_topology': 'unknown', 'unknown_values_retained': False})
    labels = {item['label']: item for item in records}
    for user in ('A', 'B'):
        first, second, after = (labels[f'{user}{n}'] for n in (1, 2, 3))
        if len({first['user_hash'], second['user_hash'], after['user_hash']}) != 1:
            codes.append('ID_USER_UNSTABLE')
        if len({first['identity_source'], second['identity_source'], after['identity_source']}) != 1:
            codes.append('ID_USER_UNSTABLE')
        membership = {
            (item['tenant_hash'], item['role'], tuple(sorted(set(item['permissions']))))
            for item in (first, second, after)
        }
        if len(membership) != 1:
            codes.append('ID_AFTER_RESTART_MISMATCH')
        if (first['user_hash'], first['tenant_hash'], first['deployment_hash'], first['profile']) != (after['user_hash'], after['tenant_hash'], after['deployment_hash'], after['profile']):
            codes.append('ID_AFTER_RESTART_MISMATCH')
    if labels['A1']['user_hash'] == labels['B1']['user_hash']:
        codes.append('ID_SAME_USER')
    if len({item['deployment_hash'] for item in records}) != 1:
        codes.append('ID_DEPLOYMENT_MISMATCH')
    if expected_binding and expected_binding.get('deployment_hash') and labels['A1']['deployment_hash'] != expected_binding.get('deployment_hash'):
        codes.append('ID_DEPLOYMENT_MISMATCH')
    if any(item['profile'] != 'company' for item in records):
        codes.append('ID_PROFILE_MISMATCH')
    if any((item['api_major'], item['api_revision']) < (expected_api_major, expected_api_revision) or item['api_major'] != expected_api_major for item in records):
        codes.append('SRC_API_INCOMPATIBLE')
    per_user_source = all(item['identity_source'] == 'process_environment' for item in records)
    same_user_instances = any(labels[f'{user}1']['instance_hash'] != labels[f'{user}2']['instance_hash'] for user in ('A', 'B'))
    shared_instance = labels['A1']['instance_hash'] == labels['B1']['instance_hash']
    if shared_instance:
        codes.extend(('ID_SHARED_INSTANCE', 'ID_SHARED_PROCESS_ACCESSKEY'))
    elif per_user_source and same_user_instances:
        codes.append('ID_USER_UNSTABLE')
    topology_path = directory.parent / 'identity-topology.json'
    topology = _strict_document(topology_path, {
        'schema_version', 'binding', 'topology', 'cross_user_routing_refused', 'simultaneous_users_confirmed',
        'provider_evidence_type', 'provider_evidence_reference', 'provider_document_checked',
    })
    topology_hash = None
    if topology:
        reference = topology.get('provider_evidence_reference')
        if (
            isinstance(reference, str) and len(reference.strip()) >= 8
            and not any(word in reference.casefold() for word in ('placeholder', 'todo', 'example.com', 'changeme'))
            and '?' not in reference and '#' not in reference
            and topology.get('provider_evidence_type') == 'provider_topology_and_routing'
            and topology.get('provider_document_checked') is True
        ):
            try: topology_hash = safe_text_hash(reference)
            except UnsafeEvidence: topology_hash = None
    provider_files, provider_refs_invalid = _reference_inventory(directory.parent / 'references' / 'identity')
    provider_evidence_present = bool(
        topology and topology_hash and provider_files
    )
    if provider_refs_invalid:
        codes.append('ATTENTION_UNKNOWN')
    provider_evidence_digest = (
        provider_files[0][1] if provider_evidence_present and len(provider_files) == 1
        else hashlib.sha256(canonical_json(provider_files)).hexdigest() if provider_evidence_present else None
    )
    topology_bound = bool(topology and expected_binding is not None and topology.get('binding') == expected_binding)
    topology_ok = bool(per_user_source and topology_bound and provider_evidence_present and topology and topology.get('topology') == 'per_user_process' and topology.get('simultaneous_users_confirmed') is True)
    routing_ok = bool(topology_ok and topology and topology.get('cross_user_routing_refused') is True)
    if not topology_ok: codes.append('ID_TOPOLOGY_UNPROVEN')
    if not routing_ok: codes.append('ID_CROSS_USER_ROUTING_UNPROVEN')
    if not codes:
        codes.append('ID_PASS_PER_USER_PROCESS')
        status = 'PASS'
    elif any(code in {'ID_SAME_USER', 'ID_USER_UNSTABLE', 'ID_SHARED_INSTANCE', 'ID_SHARED_PROCESS_ACCESSKEY', 'ID_DEPLOYMENT_MISMATCH', 'ID_PROFILE_MISMATCH', 'ID_AFTER_RESTART_MISMATCH', 'SRC_API_INCOMPATIBLE'} for code in codes):
        status = 'FAIL'
    else:
        status = 'BLOCKED'
    return phase_result(status, codes, {
        'observation_count': len(records), 'provider_topology': 'per_user_process' if topology_ok else 'unknown',
        'cross_user_routing_refused': routing_ok,
        'user_hashes_distinct': labels['A1']['user_hash'] != labels['B1']['user_hash'],
        'deployment_hash': labels['A1']['deployment_hash'],
        'tenant_hash_a': labels['A1']['tenant_hash'],
        'api_compatible': not any(code == 'SRC_API_INCOMPATIBLE' for code in codes),
        'same_qualification_tenant': labels['A1']['tenant_hash'] == labels['B1']['tenant_hash'],
        'role_a': labels['A1']['role'], 'role_b': labels['B1']['role'],
        'permission_set_a': sorted(set(labels['A1']['permissions'])),
        'permission_set_b': sorted(set(labels['B1']['permissions'])),
        'deployed_build_version': labels['A1']['build_version'] if len({item['build_version'] for item in records}) == 1 else None,
        'provider_evidence_hash': topology_hash,
        'provider_evidence_present': provider_evidence_present,
        'provider_evidence_digest': provider_evidence_digest,
        'provider_reference_invalid': provider_refs_invalid,
        'topology_binding_matches': topology_bound,
    })


def assess_tenant(identity: dict[str, Any], directory: Path, binding: dict[str, Any]) -> dict[str, Any]:
    if identity.get('status') != 'PASS':
        return phase_result('BLOCKED', ['TENANT_MIGRATION_REQUIRED'], {'tenant_hash': None})
    role_b = identity.get('role_b')
    permissions_a = set(identity.get('permission_set_a', []))
    permissions_b = set(identity.get('permission_set_b', []))
    admin_permissions_valid = {'admin', 'read', 'write'} <= permissions_a
    viewer_permissions_valid = 'read' in permissions_b and not permissions_b.intersection({'write', 'admin', 'restore', 'import'})
    editor_permissions_valid = {'read', 'write'} <= permissions_b and not permissions_b.intersection({'admin', 'restore'})
    role_permissions_valid = viewer_permissions_valid if role_b == 'viewer' else editor_permissions_valid
    if identity.get('role_a') != 'admin' or not admin_permissions_valid or not isinstance(role_b, str) or role_b not in {'viewer', 'editor'} or not role_permissions_valid or identity.get('same_qualification_tenant') is not True:
        return phase_result('FAIL', ['TENANT_MEMBER_MISMATCH'], {'tenant_hash': None})
    document = _bound_form(directory / 'tenant.json', 'tenant_membership', {
        'action', 'dedicated_non_demo', 'existing_operator_commands_used',
        'migration_result', 'maintenance_acknowledged',
    }, binding)
    if document is None or document.get('_evidence_count', 0) == 0 or document.get('_reference_invalid'):
        return phase_result('BLOCKED', ['TENANT_MIGRATION_REQUIRED', *(['ATTENTION_UNKNOWN'] if document is None and (directory / 'tenant.json').exists() else [])], {'tenant_hash': identity.get('tenant_hash_a'), 'membership_verified': True})
    facts = document['facts']
    action = facts.get('action')
    if (not isinstance(action, str) or action not in {'created', 'reused'}) or facts.get('dedicated_non_demo') is False or facts.get('existing_operator_commands_used') is False:
        return phase_result('FAIL', ['TENANT_MEMBER_MISMATCH'], {'tenant_hash': identity.get('tenant_hash_a'), 'membership_verified': True})
    migration = facts.get('migration_result')
    if migration == 'failed' or (migration == 'passed' and facts.get('maintenance_acknowledged') is not True):
        return phase_result('FAIL', ['TENANT_MIGRATION_FAIL'], {'tenant_hash': identity.get('tenant_hash_a'), 'membership_verified': True})
    if (
        facts.get('dedicated_non_demo') is not True
        or facts.get('existing_operator_commands_used') is not True
        or not isinstance(migration, str) or migration not in {'passed', 'not_required'}
    ):
        return phase_result('BLOCKED', ['TENANT_MIGRATION_REQUIRED'], {'tenant_hash': identity.get('tenant_hash_a'), 'membership_verified': True})
    reason = 'TENANT_CREATED' if action == 'created' else 'TENANT_REUSED'
    return phase_result('PASS', [reason], {
        'membership_verified': True, 'tenant_hash': identity.get('tenant_hash_a'),
        'migration_result': facts['migration_result'], 'evidence_digest': document.get('_evidence_sha256'),
    })


def _bound_form(path: Path, phase: str, keys: set[str], binding: dict[str, Any]) -> dict[str, Any] | None:
    form = _strict_document(path, {'schema_version', 'phase', 'binding', 'facts'})
    if not form or form.get('phase') != phase or not isinstance(form.get('facts'), dict) or set(form['facts']) != keys:
        return None
    if form.get('binding') != binding:
        return None
    reference_dir = path.parent / 'references' / phase
    references, invalid = _reference_inventory(reference_dir)
    digest = hashlib.sha256(canonical_json(references)).hexdigest() if references else None
    form['_evidence_count'] = len(references)
    form['_evidence_sha256'] = digest
    form['_reference_invalid'] = invalid
    form['_reference_digests'] = references
    return form


def assess_storage(directory: Path, binding: dict[str, Any], prerequisites: dict[str, Any] | None, doctor_pass: bool | None) -> dict[str, Any]:
    codes: list[str] = []
    document = _bound_form(directory / 'storage.json', 'storage', {
        'storage_kind', 'provider_reference_verified', 'all_clients_same_host', 'root_binding_exact',
        'restart_persistent', 'redeploy_persistent', 'backup_pass', 'restore_new_root_pass',
        'restore_target_is_new_empty', 'original_root_preserved',
        'attachment_enabled', 'original_attachment_sha256', 'restored_attachment_sha256', 'host_replacement',
    }, binding)
    if document is None and (directory / 'storage.json').exists():
        codes.append('ATTENTION_UNKNOWN')
    if document and document.get('_reference_invalid'):
        codes.append('ATTENTION_UNKNOWN')
    facts = document['facts'] if document else {}
    if prerequisites:
        kind = prerequisites.get('storage_kind')
        prereq_proven = (
            prerequisites.get('valid') is True
            and prerequisites.get('deployment_matches') is True
            and prerequisites.get('authorization_present') is True
        )
        provider_ref = prerequisites.get('provider_reference') if prereq_proven else None
        same_host = prerequisites.get('all_clients_same_host') if prereq_proven else None
        root_exact = prerequisites.get('root_binding_exact') if prereq_proven else None
    else:
        kind = facts.get('storage_kind')
        provider_ref = None
        same_host = facts.get('all_clients_same_host')
        root_exact = facts.get('root_binding_exact')
    if not isinstance(provider_ref, str) or len(provider_ref.strip()) < 8 or any(word in provider_ref.casefold() for word in ('placeholder', 'provider-reference-verified', 'tested', 'todo', 'changeme', 'example.com')):
        codes.append('ST_PROVIDER_SUPPORT_MISSING')
    else:
        try: reference_hash = safe_text_hash(provider_ref)
        except UnsafeEvidence: reference_hash = None; codes.append('ST_PROVIDER_SUPPORT_MISSING')
    if kind is not None and (not isinstance(kind, str) or kind not in {'local_disk', 'provider_supported_posix'}): codes.append('ST_KIND_UNSUPPORTED')
    if kind is None or same_host is None or root_exact is None: codes.append('ATTENTION_UNKNOWN')
    if same_host is False: codes.append('ST_MULTI_HOST_UNSUPPORTED')
    if root_exact is False: codes.append('ST_ROOT_MISMATCH')
    if doctor_pass is False: codes.append('ST_DOCTOR_FAIL')
    if document and document.get('_evidence_count', 0) > 0:
        boolean_facts = (
            'provider_reference_verified', 'all_clients_same_host', 'root_binding_exact',
            'restart_persistent', 'redeploy_persistent', 'backup_pass', 'restore_new_root_pass',
            'restore_target_is_new_empty', 'original_root_preserved', 'attachment_enabled',
        )
        if any(not isinstance(facts.get(key), bool) for key in boolean_facts): codes.append('ATTENTION_UNKNOWN')
        if facts.get('provider_reference_verified') is False: codes.append('ST_PROVIDER_SUPPORT_MISSING')
        if facts.get('all_clients_same_host') is False: codes.append('ST_MULTI_HOST_UNSUPPORTED')
        if facts.get('root_binding_exact') is False: codes.append('ST_ROOT_MISMATCH')
        if prerequisites and (
            facts.get('storage_kind') != prerequisites.get('storage_kind')
            or facts.get('all_clients_same_host') != prerequisites.get('all_clients_same_host')
            or facts.get('root_binding_exact') != prerequisites.get('root_binding_exact')
        ):
            codes.append('ATTENTION_UNKNOWN')
        if facts.get('restart_persistent') is False: codes.append('ST_RESTART_LOSS')
        if facts.get('redeploy_persistent') is False: codes.append('ST_REDEPLOY_LOSS')
        if facts.get('backup_pass') is False: codes.append('ST_BACKUP_FAIL')
        if facts.get('restore_new_root_pass') is False or facts.get('restore_target_is_new_empty') is False or facts.get('original_root_preserved') is False: codes.append('ST_RESTORE_FAIL')
        original_attachment = facts.get('original_attachment_sha256')
        restored_attachment = facts.get('restored_attachment_sha256')
        if facts.get('attachment_enabled') is True and (not _hex(original_attachment) or not _hex(restored_attachment)):
            codes.append('ATTENTION_UNKNOWN')
        elif facts.get('attachment_enabled') is True and original_attachment != restored_attachment:
            codes.append('ST_ATTACHMENT_MISMATCH')
        host_replacement = facts.get('host_replacement')
        if host_replacement == 'failed': codes.append('ST_REDEPLOY_LOSS')
        if not isinstance(host_replacement, str) or host_replacement not in {'passed', 'not_applicable', 'failed'}: codes.append('ATTENTION_UNKNOWN')
        unknown_keys = ('restart_persistent', 'redeploy_persistent', 'backup_pass', 'restore_new_root_pass', 'restore_target_is_new_empty', 'original_root_preserved', 'attachment_enabled', 'host_replacement')
        if any(facts.get(key) is None for key in unknown_keys): codes.append('ATTENTION_UNKNOWN')
    else:
        codes.append('ATTENTION_UNKNOWN')
    if not codes: codes = ['ST_PASS']; status = 'PASS'
    elif any(code in {'ST_KIND_UNSUPPORTED', 'ST_MULTI_HOST_UNSUPPORTED', 'ST_ROOT_MISMATCH', 'ST_DOCTOR_FAIL', 'ST_RESTART_LOSS', 'ST_REDEPLOY_LOSS', 'ST_BACKUP_FAIL', 'ST_RESTORE_FAIL', 'ST_ATTACHMENT_MISMATCH'} for code in codes): status = 'FAIL'
    else: status = 'BLOCKED'
    return phase_result(status, codes, {
        'storage_kind': kind if isinstance(kind, str) and kind in {'local_disk', 'provider_supported_posix'} else 'unknown',
        'provider_reference_hash': locals().get('reference_hash'),
        'same_host': same_host, 'root_binding_exact': root_exact,
        'doctor_storage_pass': doctor_pass, 'evidence_count': document.get('_evidence_count', 0) if document else 0,
        'evidence_digest': document.get('_evidence_sha256') if document else None,
        'original_attachment_sha256': facts.get('original_attachment_sha256') if facts.get('attachment_enabled') is True and _hex(facts.get('original_attachment_sha256')) else None,
    })


def assess_deployment(directory: Path, binding: dict[str, Any], network: dict[str, Any] | None) -> dict[str, Any]:
    codes = []
    document = _bound_form(directory / 'deployment.json', 'deployment', {
        'health_ok', 'readiness_ok',
        'frontend_backend_independent', 'runtime_api_binding', 'https', 'ingress_authentication',
        'unauthenticated_refused', 'restart_redeploy_stable', 'rolling_compatibility',
        'rollback_recovery', 'deployment_stable', 'api_compatible',
        'deployed_source_commit_matches', 'deployed_source_digest_matches',
    }, binding)
    if document is None and (directory / 'deployment.json').exists(): codes.append('ATTENTION_UNKNOWN')
    if document and document.get('_reference_invalid'): codes.append('ATTENTION_UNKNOWN')
    facts = document['facts'] if document else {}
    if network:
        facts = {**facts, **network}
    if facts.get('health_ok') is False: codes.append('DEP_HEALTH_FAIL')
    if facts.get('readiness_ok') is False: codes.append('DEP_READINESS_FAIL')
    if facts.get('frontend_backend_independent') is False or facts.get('runtime_api_binding') is False: codes.append('DEP_FRONTEND_BACKEND_MISMATCH')
    if facts.get('https') is False: codes.append('DEP_HTTPS_FAIL')
    if facts.get('ingress_authentication') is not True or facts.get('unauthenticated_refused') is None: codes.append('DEP_INGRESS_AUTH_UNPROVEN')
    if facts.get('unauthenticated_refused') is False: codes.append('DEP_UNAUTHENTICATED_ACCESS')
    if facts.get('restart_redeploy_stable') is False or facts.get('rolling_compatibility') is False or facts.get('deployment_stable') is False: codes.append('DEP_REDEPLOY_FAIL')
    if facts.get('rollback_recovery') is False: codes.append('DEP_ROLLBACK_FAIL')
    if facts.get('api_compatible') is False: codes.append('SRC_API_INCOMPATIBLE')
    if facts.get('deployed_source_commit_matches') is False or facts.get('deployed_source_digest_matches') is False: codes.append('SRC_HEAD_MISMATCH')
    required = ('health_ok', 'readiness_ok', 'frontend_backend_independent', 'runtime_api_binding', 'https', 'ingress_authentication', 'unauthenticated_refused', 'restart_redeploy_stable', 'rolling_compatibility', 'rollback_recovery', 'deployment_stable', 'api_compatible', 'deployed_source_commit_matches', 'deployed_source_digest_matches')
    if any(facts.get(key) is None for key in required): codes.append('ATTENTION_UNKNOWN')
    if any(not isinstance(facts.get(key), bool) for key in required): codes.append('ATTENTION_UNKNOWN')
    complete = document is not None and document.get('_evidence_count', 0) > 0 and all(facts.get(key) is True for key in required) and facts.get('health_ok') is True and facts.get('readiness_ok') is True
    if not codes and complete: codes = ['DEP_PASS']; status = 'PASS'
    elif any(code in {'DEP_UNAUTHENTICATED_ACCESS', 'DEP_HEALTH_FAIL', 'DEP_READINESS_FAIL', 'DEP_REDEPLOY_FAIL', 'DEP_ROLLBACK_FAIL', 'SRC_API_INCOMPATIBLE', 'SRC_HEAD_MISMATCH'} for code in codes) or any(facts.get(key) is False for key in ('https', 'frontend_backend_independent', 'runtime_api_binding', 'restart_redeploy_stable', 'rolling_compatibility', 'rollback_recovery', 'deployment_stable', 'api_compatible', 'deployed_source_commit_matches', 'deployed_source_digest_matches')): status = 'FAIL'
    else: status = 'BLOCKED'
    return phase_result(status, codes or ['DEP_INGRESS_AUTH_UNPROVEN'], {
        'health_ok': facts.get('health_ok') is True, 'readiness_ok': facts.get('readiness_ok') is True,
        'https': facts.get('https') is True, 'evidence_count': document.get('_evidence_count', 0) if document else 0,
        'evidence_digest': document.get('_evidence_sha256') if document else None,
    })


def assess_ui(directory: Path, binding: dict[str, Any], repository_ui_pass: bool | None) -> dict[str, Any]:
    document = _bound_form(directory / 'ui.json', 'ui_accessibility', {
        'major_workflows', 'role_permission_states', 'keyboard_focus', 'semantic_accessibility',
        'light_dark_high_contrast', 'reduced_motion', 'zoom_reflow', 'width_320', 'width_390',
        'native_assistive_technology',
    }, binding)
    if not document or document.get('_evidence_count', 0) == 0:
        codes = ['UI_NATIVE_ASSISTIVE_BLOCKED', 'ATTENTION_UNKNOWN']
        if document is None and (directory / 'ui.json').exists(): codes.append('ATTENTION_UNKNOWN')
        if repository_ui_pass is False:
            codes.append('UI_A11Y_AUTOMATION_FAIL')
            return phase_result('FAIL', codes, {'repository_accessibility_pass': False, 'evidence_digest': None, 'unknown_values_retained': False})
        return phase_result('BLOCKED', codes, {'repository_accessibility_pass': repository_ui_pass, 'evidence_digest': None, 'unknown_values_retained': False})
    facts = document['facts']
    if document.get('_reference_invalid'): return phase_result('BLOCKED', ['ATTENTION_UNKNOWN'], {'evidence_digest': None, 'unknown_values_retained': False})
    checks = {
        'major_workflows': 'UI_BROWSER_FAIL', 'role_permission_states': 'UI_PERMISSION_STATE_FAIL',
        'keyboard_focus': 'UI_KEYBOARD_FAIL', 'semantic_accessibility': 'UI_A11Y_AUTOMATION_FAIL',
        'zoom_reflow': 'UI_REFLOW_FAIL', 'width_320': 'UI_REFLOW_FAIL', 'width_390': 'UI_REFLOW_FAIL',
        'light_dark_high_contrast': 'UI_BROWSER_FAIL', 'reduced_motion': 'UI_BROWSER_FAIL',
    }
    codes = [code for key, code in checks.items() if facts.get(key) is False]
    if any(not isinstance(facts.get(key), bool) for key in checks): codes.append('ATTENTION_UNKNOWN')
    if facts.get('native_assistive_technology') is None: codes.append('UI_NATIVE_ASSISTIVE_BLOCKED')
    elif facts.get('native_assistive_technology') is False: codes.append('UI_A11Y_AUTOMATION_FAIL')
    if not isinstance(facts.get('native_assistive_technology'), bool): codes.append('ATTENTION_UNKNOWN')
    if repository_ui_pass is False: codes.append('UI_A11Y_AUTOMATION_FAIL')
    elif repository_ui_pass is None: codes.append('ATTENTION_UNKNOWN')
    if not codes: codes = ['UI_PASS']; status = 'PASS'
    elif any(code in {'UI_BROWSER_FAIL', 'UI_PERMISSION_STATE_FAIL', 'UI_KEYBOARD_FAIL', 'UI_A11Y_AUTOMATION_FAIL', 'UI_REFLOW_FAIL'} for code in codes): status = 'FAIL'
    else: status = 'BLOCKED'
    return phase_result(status, codes, {
        'evidence_count': document['_evidence_count'], 'evidence_digest': document['_evidence_sha256'],
        'repository_accessibility_pass': repository_ui_pass is True,
    })


def assess_performance(directory: Path, binding: dict[str, Any], repository_pass: bool | None) -> dict[str, Any]:
    document = _bound_form(directory / 'performance.json', 'performance', {
        'route_classes', 'sample_count', 'p95_latency_ms', 'threshold_ms',
        'bounded_read_only_sampling', 'large_data_path', 'ag_grid_virtualization', 'environment_class',
    }, binding)
    codes = []
    if repository_pass is False: codes.append('PERF_REPOSITORY_FAIL')
    elif repository_pass is None: codes.append('PERF_COMPANY_OBSERVATION_MISSING')
    if not document or document.get('_evidence_count', 0) == 0: codes.append('PERF_COMPANY_OBSERVATION_MISSING')
    if document and document.get('_reference_invalid'): codes.append('ATTENTION_UNKNOWN')
    if document is None:
        if (directory / 'performance.json').exists(): codes.append('ATTENTION_UNKNOWN')
    else:
        facts = document['facts']
        route_classes = facts.get('route_classes')
        routes_ok = isinstance(route_classes, list) and all(isinstance(route, str) for route in route_classes) and len(set(route_classes)) >= 3 and set(route_classes) <= {'dashboard', 'work_items', 'projects', 'planning', 'engineering', 'analytics'}
        sample_count = facts.get('sample_count')
        p95 = facts.get('p95_latency_ms')
        threshold = facts.get('threshold_ms')
        numeric = all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (sample_count, p95, threshold))
        if numeric and (p95 > threshold or p95 > 120000 or threshold < 1 or threshold > 30000): codes.append('PERF_THRESHOLD_FAIL')
        if facts.get('bounded_read_only_sampling') is False or facts.get('large_data_path') is False or facts.get('ag_grid_virtualization') is False:
            codes.append('PERF_COMPANY_OBSERVATION_MISSING')
        required = routes_ok and numeric and isinstance(sample_count, int) and not isinstance(sample_count, bool) and 3 <= sample_count <= 200 and p95 >= 0 and 1 <= threshold <= 30000 and facts.get('bounded_read_only_sampling') is True and facts.get('large_data_path') is True and facts.get('ag_grid_virtualization') is True and facts.get('environment_class') == 'company_qualification'
        if not required: codes.append('PERF_COMPANY_OBSERVATION_MISSING')
        type_valid = (
            routes_ok and numeric and isinstance(sample_count, int) and not isinstance(sample_count, bool)
            and isinstance(facts.get('bounded_read_only_sampling'), bool)
            and isinstance(facts.get('large_data_path'), bool)
            and isinstance(facts.get('ag_grid_virtualization'), bool)
            and isinstance(facts.get('environment_class'), str)
            and facts.get('environment_class') in {'company_qualification', 'development', 'test', 'production'}
        )
        if not type_valid or any(facts.get(key) is None for key in ('route_classes', 'sample_count', 'p95_latency_ms', 'threshold_ms', 'bounded_read_only_sampling', 'large_data_path', 'ag_grid_virtualization', 'environment_class')):
            codes.append('ATTENTION_UNKNOWN')
    if not codes: codes = ['PERF_PASS']; status = 'PASS'
    elif 'PERF_THRESHOLD_FAIL' in codes or 'PERF_REPOSITORY_FAIL' in codes: status = 'FAIL'
    else: status = 'BLOCKED'
    facts = document.get('facts', {}) if document else {}
    return phase_result(status, codes, {'repository_contract_pass': repository_pass is True, 'evidence_count': document.get('_evidence_count', 0) if document else 0, 'evidence_digest': document.get('_evidence_sha256') if document else None, 'sample_count': facts.get('sample_count'), 'p95_latency_ms': facts.get('p95_latency_ms'), 'threshold_ms': facts.get('threshold_ms')})


def validate_operations(path: Path, *, version: str, source_commit: str, source_digest: str, deployment_id: str | None) -> dict[str, Any]:
    labels = {drill: drill.upper() for drill in DRILLS}
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))
        from app.platform.settings import CompanyOperationsEvidence
        raw = json.loads(path.read_text(encoding='utf-8'))
        model = CompanyOperationsEvidence.model_validate(raw)
        errors = model.binding_errors(
            expected_version=version, expected_deployment_id=deployment_id,
            expected_source_commit=source_commit, expected_source_digest=source_digest,
        )
        bound = (
            model.candidate_version == version and model.verified_source_commit == source_commit
            and model.source_digest == source_digest and model.deployment_id == deployment_id
            and model.operator_id is not None
        )
        if not bound:
            return phase_result('BLOCKED', [f'OPS_{labels[drill]}_BLOCKED' for drill in DRILLS], {'drills': [], 'typed_model_valid': False})
        safe_drills = []
        for drill in model.drills:
            # Keep only the contract ID, outcome state, bounded timestamp, and hashed safe correlation IDs.
            correlation_hashes = []
            for correlation_id in drill.correlation_ids:
                correlation_hashes.append(safe_text_hash(correlation_id))
            safe_drills.append({
                'drill_id': drill.drill_id, 'status': drill.status,
                'reason_code': drill.reason_code, 'observed_at': drill.observed_at,
                'correlation_hashes': sorted(correlation_hashes), 'evidence_count': len(drill.evidence),
                'evidence_locator_hashes': sorted(safe_text_hash(item.locator) for item in drill.evidence),
            })
        codes = [f"OPS_{labels[item.drill_id]}_{'PASS' if item.status == 'PASS' else ('FAIL' if item.status == 'FAIL' else 'BLOCKED')}" for item in model.drills]
        statuses = {item.status for item in model.drills}
        phase_status = 'FAIL' if 'FAIL' in statuses else ('BLOCKED' if 'BLOCKED_EXTERNAL' in statuses or errors else 'PASS')
        return phase_result(phase_status, codes, {'drills': safe_drills, 'typed_model_valid': True})
    except Exception:
        # Validation errors can contain portions of untrusted input; never print or serialize them.
        codes = [f'OPS_{labels[drill]}_BLOCKED' for drill in DRILLS]
        if path.exists(): codes.append('ATTENTION_UNKNOWN')
        return phase_result('BLOCKED', codes, {'drills': [], 'typed_model_valid': False, 'unknown_values_retained': False})


def assess_customization(identity: dict[str, Any], *, architecture_pass: bool | None = None) -> dict[str, Any]:
    paths = identity.get('changed_paths') or []
    if not paths:
        return phase_result('PASS', ['CUST_NONE'], {'classification': 'CUST_NONE', 'changed_path_count': 0})
    lower = [str(path).casefold() for path in paths]
    if identity.get('sensitive_path_risk') is True or any(any(marker in path for marker in ('.env', 'secret', 'credential', 'key.pem')) for path in lower):
        return phase_result('FAIL', ['CUST_SECRET_RISK'], {'classification': 'CUST_SECRET_RISK', 'changed_path_count': len(paths)})
    if identity.get('api_contract_changed') is True:
        return phase_result('ATTENTION', ['CUST_API_REVISION_REQUIRED'], {'classification': 'CUST_API_REVISION_REQUIRED', 'changed_path_count': len(paths)})
    feature_paths = ('backend/app/features/', 'frontend/src/features/')
    if all(path.startswith(feature_paths) for path in lower):
        return phase_result('ATTENTION', ['CUST_SUPPORTED'], {'classification': 'CUST_SUPPORTED', 'changed_path_count': len(paths)})
    has_platform_change = any(path.startswith(('backend/app/platform/', 'frontend/src/platform/')) for path in lower)
    if has_platform_change and architecture_pass is False:
        return phase_result('FAIL', ['CUST_PLATFORM_BOUNDARY_FAIL'], {'classification': 'CUST_PLATFORM_BOUNDARY_FAIL', 'changed_path_count': len(paths)})
    if has_platform_change and architecture_pass is None:
        return phase_result('ATTENTION', ['CUST_UNKNOWN'], {'classification': 'CUST_UNKNOWN', 'changed_path_count': len(paths)})
    if has_platform_change or any(path == 'dev' or path.startswith(('scripts/', 'backend/', 'frontend/', 'contracts/', 'tests/', 'experience-lab/', 'catalog/')) for path in lower):
        classification = 'CUST_SOURCE_REVERIFY_REQUIRED'
        return phase_result('ATTENTION', [classification], {'classification': classification, 'changed_path_count': len(paths)})
    if any(path.startswith(('backend/app/platform/', 'frontend/src/platform/')) and '/features/' not in path for path in lower):
        classification = 'CUST_SOURCE_REVERIFY_REQUIRED'
    elif any(path.startswith(('application/', 'deploy/', 'config/')) or path.endswith(('.json', '.yaml', '.yml')) for path in lower):
        classification = 'CUST_CONFIG_ONLY'
    elif all(path.startswith(('docs/',)) or path in {'readme.md', 'changelog.md'} for path in lower):
        classification = 'CUST_SUPPORTED'
    elif any(path.startswith(('backend/app/features/', 'frontend/src/features/')) for path in lower):
        classification = 'CUST_SUPPORTED'
    else:
        classification = 'CUST_UNKNOWN'
    if classification == 'CUST_UNKNOWN': status = 'ATTENTION'
    elif classification == 'CUST_SOURCE_REVERIFY_REQUIRED': status = 'ATTENTION'
    else: status = 'PASS'
    return phase_result(status, [classification], {'classification': classification, 'changed_path_count': len(paths)})


def final_qualification(phases: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gates: list[dict[str, Any]] = []
    for gate_id in GATES:
        phase = phases[GATE_PHASE[gate_id]]
        passed = phase.get('status') == 'PASS'
        if passed:
            status = 'PASS'; codes = []
        else:
            status = 'FAIL' if phase.get('status') == 'FAIL' else 'BLOCKED'
            codes = list(phase.get('reason_codes') or ['ATTENTION_UNKNOWN'])
        gates.append({'id': gate_id, 'status': status, 'reason_codes': codes})
    pending = [gate for gate in gates if gate['status'] != 'PASS']
    if not pending:
        result = phase_result('ATTENTION', ['READY_FOR_OPERATOR_APPROVAL'], {'decision': 'READY_FOR_OPERATOR_APPROVAL', 'production_ready': False})
    else:
        result = phase_result('BLOCKED', ['QUAL_GATES_BLOCKED'], {'decision': 'QUALIFICATION_INCOMPLETE', 'production_ready': False})
    return result, gates
