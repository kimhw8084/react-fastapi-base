from __future__ import annotations

import hashlib
import json
import sys
import subprocess
from types import SimpleNamespace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from scripts.work_qualification import engine, source
from scripts.work_qualification import cli
from scripts.work_qualification.assess import (
    DRILLS,
    assess_customization,
    assess_deployment,
    assess_identity,
    assess_performance,
    assess_storage,
    assess_tenant,
    assess_ui,
    final_qualification,
    phase_result,
    validate_operations,
)
from scripts.work_qualification.reasons import GATE_PHASE, GATES, PHASES, REASONS, STATUSES
from scripts.work_qualification.safety import UnsafeEvidence, assert_safe, assert_safe_patch, safe_path_name
from scripts.work_qualification.source import BASE_COMMIT, BASE_TREE, configuration_observations, repository_identity
from scripts.work_qualification.store import RunStore, compact_status, ensure_private_root


VERSION = '1.0.0-rc.23'
COMMIT = 'a' * 40
DIGEST = 'b' * 64
DEPLOYMENT = 'c' * 64
BINDING = {
    'candidate_version': VERSION,
    'source_commit': COMMIT,
    'source_digest': DIGEST,
    'deployment_hash': DEPLOYMENT,
}


def hashed(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + '\n', encoding='utf-8')


def add_reference(incoming: Path, phase: str, value: str = 'd' * 64) -> None:
    path = incoming / 'references' / phase / 'evidence-provider.sha256'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + '\n', encoding='ascii')


def bound_form(incoming: Path, name: str, phase: str, facts: dict, *, binding: dict = BINDING, reference: bool = True) -> None:
    write_json(incoming / name, {'schema_version': 1, 'phase': phase, 'binding': binding, 'facts': facts})
    if reference:
        add_reference(incoming, phase)


def identity_facts() -> list[dict]:
    records = []
    for label in ('A1', 'B1', 'A2', 'B2', 'A3', 'B3'):
        user = label[0]
        records.append({
            'schema_version': 1, 'label': label, 'captured_at': '2026-09-25T12:00:00Z',
            'frontend_origin_hash': hashed('https://frontend.qual.example'),
            'api_base_hash': hashed('https://api.qual.example'),
            'http': {'runtime_config': 200, 'bootstrap': 200, 'identity_proof': 200},
            'user_hash': hashed('user-' + user),
            'instance_hash': hashed('instance-' + user),
            'deployment_hash': DEPLOYMENT,
            'profile': 'company', 'identity_source': 'process_environment',
            'build_version': VERSION, 'api_major': 1, 'api_revision': 2,
            'tenant_hash': hashed('qualification-tenant'),
            'role': 'admin' if user == 'A' else 'viewer',
            'permissions': ['admin', 'configure', 'delete', 'read', 'write'] if user == 'A' else ['read'],
        })
    return records


def valid_identity_inputs(tmp_path: Path, *, binding: dict = BINDING) -> Path:
    directory = tmp_path / 'identity-probes'
    directory.mkdir(parents=True)
    for record in identity_facts():
        write_json(directory / f"identity-{record['label']}.json", record)
    provider_document = 'e' * 64
    topology = {
        'schema_version': 1, 'binding': binding, 'topology': 'per_user_process',
        'cross_user_routing_refused': True, 'simultaneous_users_confirmed': True,
        'provider_evidence_type': 'provider_topology_and_routing',
        'provider_evidence_reference': 'Vendor control-plane topology statement QUAL-235-7',
        'provider_document_checked': True,
    }
    write_json(tmp_path / 'identity-topology.json', topology)
    evidence_path = tmp_path / 'references' / 'identity' / 'evidence-provider.sha256'
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(provider_document + '\n', encoding='ascii')
    return directory


def tenant_form(incoming: Path, *, action: str = 'reused', migration: str = 'not_required', commands: bool = True) -> None:
    evidence_sha = 'f' * 64
    bound_form(incoming, 'tenant.json', 'tenant_membership', {
        'action': action, 'dedicated_non_demo': True,
        'existing_operator_commands_used': commands, 'migration_result': migration,
        'maintenance_acknowledged': migration == 'passed',
    }, reference=False)
    path = incoming / 'references' / 'tenant_membership' / 'evidence-qualification.sha256'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(evidence_sha + '\n', encoding='ascii')


def complete_storage_facts(**changes) -> dict:
    facts = {
        'storage_kind': 'local_disk', 'provider_reference_verified': True,
        'all_clients_same_host': True, 'root_binding_exact': True,
        'restart_persistent': True, 'redeploy_persistent': True,
        'backup_pass': True, 'restore_new_root_pass': True,
        'restore_target_is_new_empty': True, 'original_root_preserved': True,
        'attachment_enabled': False, 'original_attachment_sha256': None,
        'restored_attachment_sha256': None, 'host_replacement': 'not_applicable',
    }
    facts.update(changes)
    return facts


def valid_prerequisites(**changes) -> dict:
    result = {
        'valid': True, 'deployment_matches': True, 'root_binding_exact': True,
        'authorization_present': True, 'storage_kind': 'local_disk',
        'provider_reference': 'Vendor storage manual revision 7, SQLite section 5.2',
        'all_clients_same_host': True,
    }
    result.update(changes)
    return result


def complete_deployment_facts(**changes) -> dict:
    facts = {
        'health_ok': True, 'readiness_ok': True,
        'frontend_backend_independent': True, 'runtime_api_binding': True,
        'https': True, 'ingress_authentication': True, 'unauthenticated_refused': True,
        'restart_redeploy_stable': True, 'rolling_compatibility': True,
        'rollback_recovery': True, 'deployment_stable': True, 'api_compatible': True,
        'deployed_source_commit_matches': True, 'deployed_source_digest_matches': True,
    }
    facts.update(changes)
    return facts


def complete_ui_facts(**changes) -> dict:
    facts = {
        'major_workflows': True, 'role_permission_states': True, 'keyboard_focus': True,
        'semantic_accessibility': True, 'light_dark_high_contrast': True, 'reduced_motion': True,
        'zoom_reflow': True, 'width_320': True, 'width_390': True,
        'native_assistive_technology': True,
    }
    facts.update(changes)
    return facts


def complete_performance_facts(**changes) -> dict:
    facts = {
        'route_classes': ['dashboard', 'projects', 'work_items'], 'sample_count': 30,
        'p95_latency_ms': 500, 'threshold_ms': 1200,
        'bounded_read_only_sampling': True, 'large_data_path': True,
        'ag_grid_virtualization': True, 'environment_class': 'company_qualification',
    }
    facts.update(changes)
    return facts


@pytest.mark.parametrize('status', sorted(STATUSES))
def test_status_vocabulary_and_unknown_metadata(status: str) -> None:
    code = 'CUST_NONE' if status == 'PASS' else 'ATTENTION_UNKNOWN'
    result = phase_result(status, [code])
    assert result['status'] == status
    if code == 'ATTENTION_UNKNOWN':
        assert result['unknown_values_retained'] is False
        assert result['unknown_metadata']['raw_value_retained'] is False


def test_repository_identity_is_bound_to_requested_exact_base_and_routes_dirty_to_audit() -> None:
    identity = repository_identity()
    assert identity['project'] == 'react-fastapi-base'
    assert identity['target_base_commit'] == BASE_COMMIT
    assert identity['target_base_tree'] == BASE_TREE
    assert identity['target_base_is_ancestor'] is True
    assert identity['target_base_tree_matches'] is True
    assert identity['api']['compatible'] is True
    assert 'SRC_HEAD_MISMATCH' not in identity['reason_codes']
    assert 'changed_paths' in identity and 'changed_path_hashes' in identity
    if identity['changed_paths']:
        assert identity['status'] == 'ATTENTION'
        assert 'SRC_DIRTY_WORKTREE' in identity['reason_codes']
    assert not any('content' in key for key in identity)


def test_repository_identity_creates_and_renders_a_private_run(tmp_path: Path) -> None:
    identity = repository_identity()
    assert identity['sensitive_path_risk'] is False
    assert 'secret_risk_detected' not in identity
    root = ensure_private_root(tmp_path / 'evidence', ROOT)
    store = RunStore.create(root, source=identity)
    report_path = store.directory / 'report.json'
    rendered_path = store.directory / 'report.md'
    assert report_path.is_file()
    assert rendered_path.is_file()
    report = json.loads(report_path.read_text(encoding='utf-8'))
    assert report['source']['executable_source_commit'] == identity['executable_source_commit']
    assert report['production_ready'] is False


def test_repository_identity_accepts_integrated_main_branch(monkeypatch) -> None:
    original_git = source._git

    def integrated_main(*args: str) -> str:
        if args == ('branch', '--show-current'):
            return 'main'
        return original_git(*args)

    monkeypatch.setattr(source, '_git', integrated_main)
    identity = repository_identity()
    assert identity['branch'] == 'main'
    assert identity['target_base_is_ancestor'] is True
    assert 'SRC_HEAD_MISMATCH' not in identity['reason_codes']


def test_repository_identity_still_rejects_wrong_repository_or_lineage(monkeypatch) -> None:
    monkeypatch.setattr(source, '_repository_matches', lambda: False)
    wrong_repository = repository_identity()
    assert wrong_repository['status'] == 'FAIL'
    assert 'SRC_HEAD_MISMATCH' in wrong_repository['reason_codes']

    original_run = subprocess.run

    def unrelated_lineage(args, *positional, **keywords):
        if args[:3] == ['git', 'merge-base', '--is-ancestor']:
            return SimpleNamespace(returncode=1, stdout=b'', stderr=b'')
        return original_run(args, *positional, **keywords)

    monkeypatch.setattr(subprocess, 'run', unrelated_lineage)
    wrong_lineage = repository_identity()
    assert wrong_lineage['target_base_is_ancestor'] is False
    assert wrong_lineage['status'] == 'FAIL'
    assert 'SRC_HEAD_MISMATCH' in wrong_lineage['reason_codes']


def test_missing_or_stale_release_identity_is_reported(monkeypatch, tmp_path: Path) -> None:
    identity_path = tmp_path / 'rc23-release-identity.json'
    monkeypatch.setattr(source, 'current_release_paths', lambda _root: SimpleNamespace(identity=identity_path))
    missing = repository_identity()
    assert missing['release_identity']['present'] is False
    assert 'SRC_RELEASE_IDENTITY_MISMATCH' in missing['reason_codes']

    write_json(identity_path, {
        'identity_type': 'repository_release', 'project': 'react-fastapi-base',
        'candidate_version': '1.0.0-rc.22', 'verified_source_commit': '0' * 40,
        'source_digest': '0' * 64, 'production_ready': False,
    })
    stale = repository_identity()
    assert stale['release_identity']['present'] is True
    assert stale['release_identity']['matches_current_source'] is False
    assert 'SRC_RELEASE_IDENTITY_MISMATCH' in stale['reason_codes']


def test_sensitive_changed_paths_are_redacted_and_symlink_source_is_rejected(tmp_path: Path) -> None:
    secret_path = safe_path_name('backend/config/customer-credentials.json')
    assert secret_path.startswith('[redacted-path-')
    classification = assess_customization({'changed_paths': [secret_path], 'sensitive_path_risk': True})
    assert classification['classification'] == 'CUST_SECRET_RISK'
    outside = tmp_path / 'outside.py'
    outside.write_text('private source', encoding='utf-8')
    source_dir = tmp_path / 'backend' / 'app'
    source_dir.mkdir(parents=True)
    (source_dir / 'outside_link.py').symlink_to(outside)
    from scripts.source_manifest import source_hashes
    with pytest.raises(ValueError):
        source_hashes(tmp_path)


def test_every_requested_nonpass_reason_has_a_specific_explanation_and_next_action() -> None:
    required = {
        'SRC_EXACT', 'SRC_OLD_BUILD', 'SRC_HEAD_MISMATCH', 'SRC_DIRTY_WORKTREE',
        'SRC_RELEASE_IDENTITY_MISMATCH', 'SRC_API_INCOMPATIBLE', 'SRC_UNKNOWN_DEPLOYED_BUILD',
        'CFG_NOT_QUALIFICATION', 'CFG_PROFILE_NOT_COMPANY', 'CFG_DATA_ROOT_INVALID',
        'CFG_DEPLOYMENT_ID_MISSING', 'CFG_ORIGIN_OR_HOST_INVALID', 'CFG_CSRF_INVALID',
        'CFG_SCANNER_REQUIRED_MISSING', 'CFG_QUALIFICATION_PREREQS_MISSING', 'CFG_PREFLIGHT_FAIL',
        'CFG_READINESS_FAIL', 'ID_MISSING', 'ID_SAME_USER', 'ID_USER_UNSTABLE',
        'ID_SHARED_INSTANCE', 'ID_DEPLOYMENT_MISMATCH', 'ID_PROFILE_MISMATCH',
        'ID_TOPOLOGY_UNPROVEN', 'ID_CROSS_USER_ROUTING_UNPROVEN', 'ID_AFTER_RESTART_MISMATCH',
        'ID_SHARED_PROCESS_ACCESSKEY', 'ID_PASS_PER_USER_PROCESS', 'TENANT_CREATED', 'TENANT_REUSED',
        'TENANT_MEMBER_MISMATCH', 'TENANT_MIGRATION_REQUIRED', 'TENANT_MIGRATION_FAIL',
        'ST_PROVIDER_SUPPORT_MISSING', 'ST_KIND_UNSUPPORTED', 'ST_MULTI_HOST_UNSUPPORTED',
        'ST_ROOT_MISMATCH', 'ST_DOCTOR_FAIL', 'ST_RESTART_LOSS', 'ST_REDEPLOY_LOSS',
        'ST_BACKUP_FAIL', 'ST_RESTORE_FAIL', 'ST_ATTACHMENT_MISMATCH', 'ST_PASS',
        'DEP_HEALTH_FAIL', 'DEP_READINESS_FAIL', 'DEP_FRONTEND_BACKEND_MISMATCH', 'DEP_HTTPS_FAIL',
        'DEP_INGRESS_AUTH_UNPROVEN', 'DEP_UNAUTHENTICATED_ACCESS', 'DEP_REDEPLOY_FAIL',
        'DEP_ROLLBACK_FAIL', 'DEP_PASS', 'UI_BROWSER_FAIL', 'UI_PERMISSION_STATE_FAIL',
        'UI_KEYBOARD_FAIL', 'UI_A11Y_AUTOMATION_FAIL', 'UI_REFLOW_FAIL', 'UI_NATIVE_ASSISTIVE_BLOCKED',
        'UI_PASS', 'PERF_REPOSITORY_FAIL', 'PERF_COMPANY_OBSERVATION_MISSING',
        'PERF_THRESHOLD_FAIL', 'PERF_PASS', 'CUST_NONE', 'CUST_CONFIG_ONLY', 'CUST_SUPPORTED',
        'CUST_SOURCE_REVERIFY_REQUIRED', 'CUST_API_REVISION_REQUIRED', 'CUST_PLATFORM_BOUNDARY_FAIL',
        'CUST_SECRET_RISK', 'CUST_UNKNOWN', 'ATTENTION_UNKNOWN',
    }
    required.update(f'OPS_{drill.upper()}_{status}' for drill in DRILLS for status in ('PASS', 'FAIL', 'BLOCKED'))
    assert required <= set(REASONS)
    assert all(REASONS[code].explanation and REASONS[code].next_action for code in required)


def test_source_reason_codes_old_build_head_mismatch_and_unknown_build() -> None:
    candidate = {'candidate_version': VERSION, 'reason_codes': ['SRC_DIRTY_WORKTREE']}
    old = engine._source_reason(candidate, {'backend_build_version': '1.0.0-rc.22'}, {'reason_codes': []})
    assert 'SRC_OLD_BUILD' in old
    head = engine._source_reason(candidate, {'backend_build_version': VERSION}, {'reason_codes': ['SRC_HEAD_MISMATCH']})
    assert 'SRC_HEAD_MISMATCH' in head
    unknown = engine._source_reason(candidate, None, {'reason_codes': []})
    assert 'SRC_UNKNOWN_DEPLOYED_BUILD' in unknown


@pytest.mark.parametrize(
    ('mutation', 'reason', 'status'),
    [
        ('same_user', 'ID_SAME_USER', 'FAIL'),
        ('unstable_user', 'ID_USER_UNSTABLE', 'FAIL'),
        ('shared_instance', 'ID_SHARED_INSTANCE', 'FAIL'),
        ('deployment', 'ID_DEPLOYMENT_MISMATCH', 'FAIL'),
        ('profile', 'ID_PROFILE_MISMATCH', 'FAIL'),
        ('restart', 'ID_AFTER_RESTART_MISMATCH', 'FAIL'),
        ('api', 'SRC_API_INCOMPATIBLE', 'FAIL'),
    ],
)
def test_identity_rejects_inconsistent_real_user_observations(tmp_path: Path, mutation: str, reason: str, status: str) -> None:
    directory = valid_identity_inputs(tmp_path)
    records = identity_facts()
    selected = next(record for record in records if record['label'] == 'B1')
    if mutation == 'same_user':
        for record in records:
            if record['label'].startswith('B'):
                record['user_hash'] = hashed('user-A')
    elif mutation == 'unstable_user':
        next(record for record in records if record['label'] == 'B3')['user_hash'] = hashed('different-user')
    elif mutation == 'shared_instance':
        for record in records:
            if record['label'].startswith('B'):
                record['instance_hash'] = hashed('instance-A')
    elif mutation == 'deployment':
        selected['deployment_hash'] = hashed('another-deployment')
    elif mutation == 'profile':
        selected['profile'] = 'development'
    elif mutation == 'restart':
        next(record for record in records if record['label'] == 'A3')['tenant_hash'] = hashed('different-tenant')
    elif mutation == 'api':
        selected['api_revision'] = 1
    for record in records:
        write_json(directory / f"identity-{record['label']}.json", record)
    result = assess_identity(directory, expected_api_major=1, expected_api_revision=2, expected_binding=BINDING)
    assert result['status'] == status
    assert reason in result['reason_codes']


def test_identity_pass_requires_provider_digest_and_exact_source_binding(tmp_path: Path) -> None:
    directory = valid_identity_inputs(tmp_path)
    result = assess_identity(directory, expected_api_major=1, expected_api_revision=2, expected_binding=BINDING)
    assert result['status'] == 'PASS'
    assert 'ID_PASS_PER_USER_PROCESS' in result['reason_codes']
    assert result['provider_evidence_present'] is True
    assert result['provider_evidence_digest'] == 'e' * 64
    assert result['user_hashes_distinct'] is True

    topology_path = tmp_path / 'identity-topology.json'
    topology = json.loads(topology_path.read_text())
    topology['binding'] = {**BINDING, 'source_digest': '0' * 64}
    write_json(topology_path, topology)
    stale = assess_identity(directory, expected_api_major=1, expected_api_revision=2, expected_binding=BINDING)
    assert stale['status'] == 'BLOCKED'
    assert stale['topology_binding_matches'] is False
    assert 'ID_TOPOLOGY_UNPROVEN' in stale['reason_codes']


def test_identity_blocks_missing_fake_and_raw_provider_evidence(tmp_path: Path) -> None:
    directory = valid_identity_inputs(tmp_path)
    topology_path = tmp_path / 'identity-topology.json'
    topology = json.loads(topology_path.read_text())
    topology.update({
        'provider_evidence_reference': 'provider-reference-verified',
        'provider_evidence_type': 'unknown', 'provider_document_sha256': None,
        'provider_document_checked': None,
    })
    write_json(topology_path, topology)
    fake = assess_identity(directory, expected_api_major=1, expected_api_revision=2, expected_binding=BINDING)
    assert fake['status'] == 'BLOCKED'
    assert fake['provider_evidence_present'] is False

    reference = tmp_path / 'references' / 'identity' / 'evidence-provider.sha256'
    reference.write_text('authorization=neverpersist\n')
    raw = assess_identity(directory, expected_api_major=1, expected_api_revision=2, expected_binding=BINDING)
    assert raw['status'] == 'BLOCKED'
    assert raw['provider_reference_invalid'] is True
    assert 'ATTENTION_UNKNOWN' in raw['reason_codes']


@pytest.mark.parametrize(
    ('field', 'value', 'reason'),
    [
        ('storage_kind', 'object_store', 'ST_KIND_UNSUPPORTED'),
        ('all_clients_same_host', False, 'ST_MULTI_HOST_UNSUPPORTED'),
        ('root_binding_exact', False, 'ST_ROOT_MISMATCH'),
        ('restart_persistent', False, 'ST_RESTART_LOSS'),
        ('redeploy_persistent', False, 'ST_REDEPLOY_LOSS'),
        ('backup_pass', False, 'ST_BACKUP_FAIL'),
        ('restore_new_root_pass', False, 'ST_RESTORE_FAIL'),
        ('restore_target_is_new_empty', False, 'ST_RESTORE_FAIL'),
        ('original_root_preserved', False, 'ST_RESTORE_FAIL'),
        ('host_replacement', 'failed', 'ST_REDEPLOY_LOSS'),
    ],
)
def test_storage_reports_specific_observed_failures(tmp_path: Path, field: str, value, reason: str) -> None:
    incoming = tmp_path / 'incoming'
    facts = complete_storage_facts(**{field: value})
    bound_form(incoming, 'storage.json', 'storage', facts)
    prereqs = valid_prerequisites(**{field: value}) if field in {'storage_kind', 'all_clients_same_host', 'root_binding_exact'} else valid_prerequisites()
    result = assess_storage(incoming, BINDING, prereqs, True)
    assert result['status'] == 'FAIL'
    assert reason in result['reason_codes']


def test_storage_pass_and_rejects_placeholder_or_unsafe_restore(tmp_path: Path) -> None:
    incoming = tmp_path / 'incoming'
    bound_form(incoming, 'storage.json', 'storage', complete_storage_facts())
    result = assess_storage(incoming, BINDING, valid_prerequisites(), True)
    assert result['status'] == 'PASS'
    assert result['reason_codes'] == ['ST_PASS']

    fake = assess_storage(incoming, BINDING, valid_prerequisites(provider_reference='provider-reference-verified'), True)
    assert fake['status'] == 'BLOCKED'
    assert 'ST_PROVIDER_SUPPORT_MISSING' in fake['reason_codes']

    no_doctor = assess_storage(incoming, BINDING, valid_prerequisites(), False)
    assert no_doctor['status'] == 'FAIL'
    assert 'ST_DOCTOR_FAIL' in no_doctor['reason_codes']

    mismatch = complete_storage_facts(
        attachment_enabled=True, original_attachment_sha256='1' * 64,
        restored_attachment_sha256='2' * 64,
    )
    bound_form(incoming, 'storage.json', 'storage', mismatch)
    mismatch_result = assess_storage(incoming, BINDING, valid_prerequisites(), True)
    assert mismatch_result['status'] == 'FAIL'
    assert 'ST_ATTACHMENT_MISMATCH' in mismatch_result['reason_codes']


@pytest.mark.parametrize(
    ('field', 'value', 'reason', 'status'),
    [
        ('health_ok', False, 'DEP_HEALTH_FAIL', 'FAIL'),
        ('readiness_ok', False, 'DEP_READINESS_FAIL', 'FAIL'),
        ('frontend_backend_independent', False, 'DEP_FRONTEND_BACKEND_MISMATCH', 'FAIL'),
        ('https', False, 'DEP_HTTPS_FAIL', 'FAIL'),
        ('ingress_authentication', None, 'DEP_INGRESS_AUTH_UNPROVEN', 'BLOCKED'),
        ('unauthenticated_refused', False, 'DEP_UNAUTHENTICATED_ACCESS', 'FAIL'),
        ('restart_redeploy_stable', False, 'DEP_REDEPLOY_FAIL', 'FAIL'),
        ('rolling_compatibility', False, 'DEP_REDEPLOY_FAIL', 'FAIL'),
        ('rollback_recovery', False, 'DEP_ROLLBACK_FAIL', 'FAIL'),
        ('api_compatible', False, 'SRC_API_INCOMPATIBLE', 'FAIL'),
        ('deployed_source_commit_matches', False, 'SRC_HEAD_MISMATCH', 'FAIL'),
    ],
)
def test_deployment_matrix(tmp_path: Path, field: str, value, reason: str, status: str) -> None:
    incoming = tmp_path / 'incoming'
    bound_form(incoming, 'deployment.json', 'deployment', complete_deployment_facts(**{field: value}))
    result = assess_deployment(incoming, BINDING, None)
    assert result['status'] == status
    assert reason in result['reason_codes']


def test_deployment_pass_and_missing_ingress_is_blocked(tmp_path: Path) -> None:
    incoming = tmp_path / 'incoming'
    bound_form(incoming, 'deployment.json', 'deployment', complete_deployment_facts())
    assert assess_deployment(incoming, BINDING, None)['reason_codes'] == ['DEP_PASS']
    bound_form(incoming, 'deployment.json', 'deployment', complete_deployment_facts(ingress_authentication=None), reference=False)
    blocked = assess_deployment(incoming, BINDING, None)
    assert blocked['status'] == 'BLOCKED'
    assert 'DEP_INGRESS_AUTH_UNPROVEN' in blocked['reason_codes']

    stale_binding = {**BINDING, 'source_digest': '0' * 64}
    bound_form(incoming, 'deployment.json', 'deployment', complete_deployment_facts(), binding=stale_binding)
    stale = assess_deployment(incoming, BINDING, None)
    assert stale['status'] == 'BLOCKED'
    assert 'ATTENTION_UNKNOWN' in stale['reason_codes']


@pytest.mark.parametrize(
    ('field', 'value', 'reason', 'status'),
    [
        ('major_workflows', False, 'UI_BROWSER_FAIL', 'FAIL'),
        ('role_permission_states', False, 'UI_PERMISSION_STATE_FAIL', 'FAIL'),
        ('keyboard_focus', False, 'UI_KEYBOARD_FAIL', 'FAIL'),
        ('semantic_accessibility', False, 'UI_A11Y_AUTOMATION_FAIL', 'FAIL'),
        ('width_320', False, 'UI_REFLOW_FAIL', 'FAIL'),
        ('width_390', False, 'UI_REFLOW_FAIL', 'FAIL'),
        ('native_assistive_technology', None, 'UI_NATIVE_ASSISTIVE_BLOCKED', 'BLOCKED'),
        ('native_assistive_technology', False, 'UI_A11Y_AUTOMATION_FAIL', 'FAIL'),
    ],
)
def test_ui_accessibility_matrix(tmp_path: Path, field: str, value, reason: str, status: str) -> None:
    incoming = tmp_path / 'incoming'
    bound_form(incoming, 'ui.json', 'ui_accessibility', complete_ui_facts(**{field: value}))
    result = assess_ui(incoming, BINDING, True)
    assert result['status'] == status
    assert reason in result['reason_codes']


def test_ui_requires_repository_browser_a11y_and_real_company_evidence(tmp_path: Path) -> None:
    incoming = tmp_path / 'incoming'
    bound_form(incoming, 'ui.json', 'ui_accessibility', complete_ui_facts())
    assert assess_ui(incoming, BINDING, True)['status'] == 'PASS'
    assert assess_ui(incoming, BINDING, False)['status'] == 'FAIL'
    missing_local = assess_ui(incoming, BINDING, None)
    assert missing_local['status'] == 'BLOCKED'
    assert 'ATTENTION_UNKNOWN' in missing_local['reason_codes']
    assert assess_ui(tmp_path / 'missing', BINDING, None)['status'] == 'BLOCKED'


def test_performance_regression_missing_and_pass(tmp_path: Path) -> None:
    incoming = tmp_path / 'incoming'
    bound_form(incoming, 'performance.json', 'performance', complete_performance_facts())
    assert assess_performance(incoming, BINDING, True)['status'] == 'PASS'
    assert assess_performance(incoming, BINDING, None)['status'] == 'BLOCKED'
    bound_form(incoming, 'performance.json', 'performance', complete_performance_facts(p95_latency_ms=1500))
    failed = assess_performance(incoming, BINDING, True)
    assert failed['status'] == 'FAIL'
    assert 'PERF_THRESHOLD_FAIL' in failed['reason_codes']
    bound_form(incoming, 'performance.json', 'performance', complete_performance_facts(p95_latency_ms='unknown'))
    malformed = assess_performance(incoming, BINDING, True)
    assert malformed['status'] == 'BLOCKED'
    assert 'ATTENTION_UNKNOWN' in malformed['reason_codes']


def test_tenant_needs_real_membership_and_existing_operator_evidence(tmp_path: Path) -> None:
    directory = valid_identity_inputs(tmp_path)
    identity = assess_identity(directory, expected_api_major=1, expected_api_revision=2, expected_binding=BINDING)
    tenant_form(tmp_path, action='created', migration='passed')
    result = assess_tenant(identity, tmp_path, BINDING)
    assert result['status'] == 'PASS'
    assert result['reason_codes'] == ['TENANT_CREATED']
    assert result['migration_result'] == 'passed'

    tenant_form(tmp_path, action='reused', migration='failed')
    failed = assess_tenant(identity, tmp_path, BINDING)
    assert failed['status'] == 'FAIL'
    assert 'TENANT_MIGRATION_FAIL' in failed['reason_codes']

    tenant_form(tmp_path, action='reused', migration='not_required', commands=False)
    mismatch = assess_tenant(identity, tmp_path, BINDING)
    assert mismatch['status'] == 'FAIL'
    assert 'TENANT_MEMBER_MISMATCH' in mismatch['reason_codes']

    identity['permission_set_b'] = ['read', 'write', 'admin']
    privilege_mismatch = assess_tenant(identity, tmp_path, BINDING)
    assert privilege_mismatch['status'] == 'FAIL'
    assert 'TENANT_MEMBER_MISMATCH' in privilege_mismatch['reason_codes']


def operations_document(*, status_by_drill: dict[str, str] | None = None, **bindings) -> dict:
    status_by_drill = status_by_drill or {}
    records = []
    for drill in DRILLS:
        status = status_by_drill.get(drill, 'PASS')
        evidence = [] if status != 'PASS' else [{
            'kind': 'operations_report', 'locator': f'evidence/company/{drill}.json',
            'evidence_id': f'company-{drill}', 'issuer': 'qualification-operator',
        }]
        records.append({
            'drill_id': drill, 'status': status, 'evidence': evidence,
            'correlation_ids': [f'corr-{drill}'], 'observed_at': '2026-09-25T12:00:00Z',
            'outcome': 'Observed the declared qualification drill and verified its expected bounded recovery.',
            'reason_code': 'drill_passed' if status == 'PASS' else 'company_staging_required',
        })
    result = {
        'schema_version': 1, 'evidence_type': 'company_operations_drill',
        'deployment_id': 'qualification-deployment-235', 'candidate_version': VERSION,
        'verified_source_commit': COMMIT, 'source_digest': DIGEST,
        'operator_id': 'qualification-operator', 'created_at': '2026-09-25T12:00:00Z',
        'drills': records,
    }
    result.update(bindings)
    return result


def test_all_seven_operations_drills_pass_fail_and_block(tmp_path: Path) -> None:
    path = tmp_path / 'ops.json'
    write_json(path, operations_document())
    result = validate_operations(path, version=VERSION, source_commit=COMMIT, source_digest=DIGEST, deployment_id='qualification-deployment-235')
    assert result['status'] == 'PASS'
    assert len(result['drills']) == 7
    assert all(code.endswith('_PASS') for code in result['reason_codes'])
    assert 'corr-startup_restart' not in json.dumps(result)

    for drill in DRILLS:
        write_json(path, operations_document(status_by_drill={drill: 'FAIL'}))
        failed = validate_operations(path, version=VERSION, source_commit=COMMIT, source_digest=DIGEST, deployment_id='qualification-deployment-235')
        assert failed['status'] == 'FAIL'
        assert f'OPS_{drill.upper()}_FAIL' in failed['reason_codes']
        write_json(path, operations_document(status_by_drill={drill: 'BLOCKED_EXTERNAL'}))
        blocked = validate_operations(path, version=VERSION, source_commit=COMMIT, source_digest=DIGEST, deployment_id='qualification-deployment-235')
        assert blocked['status'] == 'BLOCKED'
        assert f'OPS_{drill.upper()}_BLOCKED' in blocked['reason_codes']


@pytest.mark.parametrize(
    'bindings',
    [
        {'candidate_version': '1.0.0-rc.22'},
        {'verified_source_commit': '0' * 40},
        {'source_digest': '0' * 64},
        {'operator_id': 'placeholder-operator'},
    ],
)
def test_operations_reject_stale_or_placeholder_source_binding(tmp_path: Path, bindings: dict) -> None:
    path = tmp_path / 'ops.json'
    write_json(path, operations_document(**bindings))
    result = validate_operations(path, version=VERSION, source_commit=COMMIT, source_digest=DIGEST, deployment_id='qualification-deployment-235')
    assert result['status'] == 'BLOCKED'
    assert result['typed_model_valid'] is False
    assert not any(code.endswith('_PASS') for code in result['reason_codes'])


def test_operations_reject_fake_pass_and_secret_bearing_input(tmp_path: Path) -> None:
    path = tmp_path / 'ops.json'
    fake = operations_document()
    fake['drills'][0]['reason_code'] = 'company_staging_required'
    write_json(path, fake)
    rejected = validate_operations(path, version=VERSION, source_commit=COMMIT, source_digest=DIGEST, deployment_id='qualification-deployment-235')
    assert rejected['status'] == 'BLOCKED'
    assert rejected['typed_model_valid'] is False

    secret = operations_document()
    secret['drills'][0]['correlation_ids'] = ['Authorization: Bearer ' + '_'.join(['neverpersist', '123456789'])]
    write_json(path, secret)
    rejected_secret = validate_operations(path, version=VERSION, source_commit=COMMIT, source_digest=DIGEST, deployment_id='qualification-deployment-235')
    assert rejected_secret['status'] == 'BLOCKED'
    assert 'neverpersist' not in json.dumps(rejected_secret)


def test_private_source_patch_scanner_rejects_concrete_secrets_and_accepts_safe_source() -> None:
    assert_safe_patch("secret = make_document()\nprobe = 'AccessKey' + '=' + value\n")
    assert_safe_patch("# Authorization field is omitted from every report.\n")
    for patch in (
        'AccessKey' + '=' + 'superSecretValueLongEnoughToMatch123456' + '\n',
        'Authorization: Bearer ' + 'abcdefghijklmnopqrstuvwxyz0123456789' + '\n',
        'https://api.example.test/resource' + '?' + 'session_token=private-value' + '\n',
        'eyJabcdefghijk' + '.' + 'abcdefghijk' + '.' + 'abcdefghijk' + '\n',
    ):
        with pytest.raises(UnsafeEvidence):
            assert_safe_patch(patch)


@pytest.mark.parametrize('material', [
    'AccessKey=ak_live_example_1234567890',
    'cookie=sessionid_example_1234567890',
    'Authorization: Bearer abcdefghijklmnopqrstuvwxyz0123456789',
    'eyJabcdefghijk.abcdefghijk.abcdefghijk',
    'csrf_token=csrf_example_1234567890',
    'password=password_example_1234567890',
    'session_token=session_example_1234567890',
    'token=token_example_1234567890',
    'secret=secret_example_1234567890',
])
def test_concrete_credential_material_is_rejected_from_evidence_values(material: str) -> None:
    with pytest.raises(UnsafeEvidence):
        assert_safe({'observation': material})


@pytest.mark.parametrize('key', [
    'AccessKey', 'cookie', 'Authorization', 'jwt', 'csrf_token',
    'password', 'session_token', 'token', 'secret',
])
def test_credential_named_evidence_fields_are_rejected(key: str) -> None:
    with pytest.raises(UnsafeEvidence):
        assert_safe({key: 'redacted'})


def test_customization_source_checks_use_sanitized_environment_and_private_patch(tmp_path: Path, monkeypatch) -> None:
    store, _ = make_initial_state(tmp_path)
    source_document = {
        'changed_paths': ['backend/app/features/example/service.py'],
        'source_digest': DIGEST,
    }
    monkeypatch.setenv('QUALIFICATION_PROVIDER_SECRET', 'do-not-inherit-this-value')
    invocations = []

    def check(name, command, *, cwd, environment, timeout=300):
        invocations.append((name, dict(environment)))
        return {'check': name, 'status': 'PASS'}

    monkeypatch.setattr(engine, '_run_local_check', check)
    monkeypatch.setattr(engine, '_private_change_patch', lambda _: b'private reviewed patch\n')
    result = engine._source_local_checks(store, source_document, None)
    assert result['status'] == 'PASS'
    assert result['patch_status'] == 'PASS'
    assert (store.evidence / 'customization.patch').read_bytes() == b'private reviewed patch\n'
    assert invocations and all('QUALIFICATION_PROVIDER_SECRET' not in env for _, env in invocations)
    assert all(env['BASE_ENVIRONMENT'] == 'test' for _, env in invocations)


def test_customization_classification_and_api_impact() -> None:
    assert assess_customization({'changed_paths': []})['classification'] == 'CUST_NONE'
    config = assess_customization({'changed_paths': ['application/navigation.json']})
    assert config['classification'] == 'CUST_CONFIG_ONLY'
    supported = assess_customization({'changed_paths': ['backend/app/features/work_items/service.py']})
    assert supported['classification'] == 'CUST_SUPPORTED'
    source_change = assess_customization({'changed_paths': ['backend/app/platform/security.py']}, architecture_pass=True)
    assert source_change['classification'] == 'CUST_SOURCE_REVERIFY_REQUIRED'
    api_change = assess_customization({'changed_paths': ['backend/app/platform/router.py'], 'api_contract_changed': True})
    assert api_change['classification'] == 'CUST_API_REVISION_REQUIRED'
    boundary = assess_customization({'changed_paths': ['backend/app/platform/security.py']}, architecture_pass=False)
    assert boundary['classification'] == 'CUST_PLATFORM_BOUNDARY_FAIL'
    secret = assess_customization({'changed_paths': ['.env.production']})
    assert secret['status'] == 'FAIL'
    assert secret['classification'] == 'CUST_SECRET_RISK'


def test_configuration_is_allowlisted_and_never_retains_secret_values(tmp_path: Path, monkeypatch) -> None:
    prereq = tmp_path / 'qualification-prerequisites.json'
    prereq.write_text('{}')
    monkeypatch.setenv('BASE_ENVIRONMENT', 'qualification')
    monkeypatch.setenv('BASE_PROFILE', 'company')
    monkeypatch.setenv('BASE_DATA_ROOT', str(tmp_path / 'persistent'))
    monkeypatch.setenv('BASE_DEPLOYMENT_ID', 'deployment-235')
    monkeypatch.setenv('BASE_ALLOWED_ORIGINS', json.dumps(['https://frontend.qual.example']))
    monkeypatch.setenv('BASE_ALLOWED_HOSTS', json.dumps(['frontend.qual.example']))
    monkeypatch.setenv('BASE_CSRF_SECRET', 'secretSentinelDoNotPersist987654321')
    monkeypatch.setenv('BASE_ATTACHMENT_UPLOAD_MODE', 'trusted_types')
    monkeypatch.setenv('BASE_QUALIFICATION_PREREQUISITES_FILE', str(prereq))
    monkeypatch.setenv('BASE_QUALIFICATION_FILE', str(tmp_path / 'final.json'))
    monkeypatch.setenv('BASE_ENABLE_DOCS', 'false')
    observed = configuration_observations()
    serialized = json.dumps(observed)
    assert observed['request_integrity_strength'] == 'strong'
    assert observed['deployment_hash'] == hashed('deployment-235')
    assert 'secretSentinel' not in serialized
    assert 'frontend.qual.example' not in serialized

    monkeypatch.setenv('BASE_CSRF_SECRET', 'weak')
    bad = configuration_observations()
    assert 'CFG_CSRF_INVALID' in bad['reason_codes']
    monkeypatch.setenv('BASE_ENABLE_DOCS', 'true')
    exposed = configuration_observations()
    assert 'CFG_DOCS_EXPOSED' in exposed['reason_codes']


@pytest.mark.parametrize(
    ('field', 'value', 'reason'),
    [
        ('BASE_ENVIRONMENT', 'development', 'CFG_NOT_QUALIFICATION'),
        ('BASE_PROFILE', 'development', 'CFG_PROFILE_NOT_COMPANY'),
        ('BASE_DATA_ROOT', 'relative/data', 'CFG_DATA_ROOT_INVALID'),
        ('BASE_DEPLOYMENT_ID', 'local', 'CFG_DEPLOYMENT_ID_MISSING'),
        ('BASE_ALLOWED_ORIGINS', '["http://frontend.qual.example"]', 'CFG_ORIGIN_OR_HOST_INVALID'),
        ('BASE_CSRF_SECRET', 'weak', 'CFG_CSRF_INVALID'),
        ('BASE_ATTACHMENT_UPLOAD_MODE', 'scanner_required', 'CFG_SCANNER_REQUIRED_MISSING'),
        ('BASE_QUALIFICATION_PREREQUISITES_FILE', '', 'CFG_QUALIFICATION_PREREQS_MISSING'),
    ],
)
def test_configuration_preflight_reason_matrix(tmp_path: Path, monkeypatch, field: str, value: str, reason: str) -> None:
    prereq = tmp_path / 'prereq.json'
    prereq.write_text('{}')
    baseline = {
        'BASE_ENVIRONMENT': 'qualification', 'BASE_PROFILE': 'company',
        'BASE_DATA_ROOT': str(tmp_path / 'persistent'), 'BASE_DEPLOYMENT_ID': 'deployment-235',
        'BASE_ALLOWED_ORIGINS': '["https://frontend.qual.example"]',
        'BASE_ALLOWED_HOSTS': '["frontend.qual.example"]',
        'BASE_CSRF_SECRET': 'configured-but-never-emitted-csrf-value-235',
        'BASE_ATTACHMENT_UPLOAD_MODE': 'trusted_types',
        'BASE_QUALIFICATION_PREREQUISITES_FILE': str(prereq),
    }
    for key, item in baseline.items(): monkeypatch.setenv(key, item)
    monkeypatch.setenv(field, value)
    result = configuration_observations()
    assert reason in result['reason_codes']
    assert 'configured-but-never-emitted' not in json.dumps(result)


def test_reference_mode_hashes_external_file_without_copying_path_or_contents(tmp_path: Path) -> None:
    store, state = make_initial_state(tmp_path)
    source_file = tmp_path / 'approved-provider-record.txt'
    source_content = 'AccessKey' + '=' + '_'.join(['neverpersist', '98123456']) + ' and provider qualification notes'
    source_file.write_text(source_content, encoding='utf-8')
    cli._add_reference(store, 'identity', str(source_file.resolve()))
    reference = store.incoming / 'references' / 'identity' / 'evidence-001.sha256'
    assert reference.read_text().strip() == hashlib.sha256(source_content.encode()).hexdigest()
    assert source_content not in reference.read_text()
    assert str(source_file) not in (store.directory / 'events.jsonl').read_text()
    assert 'neverpersist' not in (store.directory / 'events.jsonl').read_text()
    assert source_file.is_file()

    with pytest.raises(ValueError):
        cli._add_reference(store, 'unknown', str(source_file.resolve()))
    with pytest.raises(ValueError):
        cli._add_reference(store, 'identity', str(reference.resolve()))


def test_operator_private_evidence_root_is_remembered_without_repeat_prompt(tmp_path: Path, monkeypatch) -> None:
    hint = tmp_path / 'user-config' / 'work-qualification-root.json'
    monkeypatch.setattr(cli, '_root_hint_path', lambda: hint)
    monkeypatch.delenv('BASE_WORK_QUALIFICATION_EVIDENCE_ROOT', raising=False)
    selected = ensure_private_root(tmp_path / 'persistent-private-root', ROOT)
    cli._remember_root(selected)
    monkeypatch.setattr(cli.sys, 'stdin', type('NonInteractiveInput', (), {'isatty': lambda self: False})())
    assert cli._remembered_root() == str(selected)
    assert cli._root() == selected
    assert hint.stat().st_mode & 0o077 == 0


def make_initial_state(tmp_path: Path):
    source_doc = {
        'target_base_commit': BASE_COMMIT, 'candidate_version': VERSION,
        'source_digest': DIGEST, 'executable_source_commit': COMMIT,
    }
    root = ensure_private_root(tmp_path / 'operator-private', ROOT)
    store = RunStore.create(root, source=source_doc)
    state = store.read_state()
    state['gates'] = [{'id': gate, 'status': 'BLOCKED', 'reason_codes': ['ATTENTION_UNKNOWN']} for gate in GATES]
    state['phases']['customization']['classification'] = 'CUST_CONFIG_ONLY'
    state['observations'] = {'configuration': {'deployment_hash': DEPLOYMENT}}
    state['decision'] = 'QUALIFICATION_INCOMPLETE'
    state['production_ready'] = False
    return store, state


def test_render_is_stable_across_canonical_state_reload(tmp_path: Path) -> None:
    store, state = make_initial_state(tmp_path)
    phase_map = state['phases']
    state['phases'] = {phase: phase_map[phase] for phase in PHASES}

    first_handoff = store.render(state)
    first_files = {
        name: (store.directory / name).read_bytes()
        for name in ('report.json', 'report.md', 'next.txt', 'inventory.json', 'handoff.txt')
    }

    reloaded = json.loads(json.dumps(state, sort_keys=True))
    second_handoff = store.render(reloaded)
    second_files = {
        name: (store.directory / name).read_bytes()
        for name in first_files
    }

    assert first_handoff == second_handoff
    assert first_files == second_files


def test_final_all_pass_maps_only_existing_eight_gates_and_never_approves() -> None:
    phases = {phase: {'status': 'PASS', 'reason_codes': []} for phase in set(GATE_PHASE.values())}
    result, gates = final_qualification(phases)
    assert [gate['id'] for gate in gates] == list(GATES)
    assert all(gate['status'] == 'PASS' for gate in gates)
    assert result['decision'] == 'READY_FOR_OPERATOR_APPROVAL'
    assert result['production_ready'] is False
    assert 'approved_by' not in result and 'approved_at' not in result


def test_identity_blocker_stops_later_passing_phases_and_operator_actions(tmp_path: Path) -> None:
    identity = {'status': 'FAIL', 'reason_codes': ['ID_SHARED_INSTANCE']}
    later = {'status': 'PASS', 'reason_codes': ['ST_PASS']}
    guarded = engine._require_prior_pass(later, ('identity',), {'identity': identity})
    assert guarded['status'] == 'BLOCKED'
    assert guarded['reason_codes'] == ['ID_SHARED_INSTANCE']
    assert guarded['operator_action_state'] == 'WAITING_FOR_OPERATOR_ACTION'

    store, state = make_initial_state(tmp_path)
    state['phases']['identity'] = {'status': 'BLOCKED', 'reason_codes': ['ID_TOPOLOGY_UNPROVEN']}
    state['phases']['storage'] = {'status': 'BLOCKED', 'reason_codes': ['ST_PROVIDER_SUPPORT_MISSING']}
    next_steps = store._next(state)
    assert 'ID_TOPOLOGY_UNPROVEN' in next_steps
    assert 'storage' not in next_steps.casefold()
    assert 'ST_PROVIDER_SUPPORT_MISSING' not in next_steps


def test_handoff_is_deterministic_bounded_and_secret_free(tmp_path: Path) -> None:
    store, state = make_initial_state(tmp_path)
    first = store.render(state)
    second = store._handoff(state, store._inventory()['bundle_sha256'])
    assert first == second
    assert len(first) <= 300
    assert first.startswith('RFBWQ1 v=rc23 src=')
    assert f"run={store.run_id[-8:]}" in first
    assert 'bundle=' in first and '://' not in first and '/' not in first
    assert_safe({'handoff': first}, compact=True)

    pass_phases = {phase: {'status': 'PASS', 'reason_codes': []} for phase in set(GATE_PHASE.values())}
    ready, gates = final_qualification(pass_phases)
    state['decision'] = ready['decision']
    state['gates'] = gates
    state['phases']['customization']['classification'] = 'CUST_SUPPORTED'
    approved = store._handoff(state, '1' * 64)
    assert 'READY_FOR_OPERATOR_APPROVAL' in approved
    assert len(approved) <= 300
    assert 'production_ready' not in approved


def test_run_resume_append_only_idempotent_and_secret_negative_controls(tmp_path: Path, monkeypatch) -> None:
    store, state = make_initial_state(tmp_path)
    monkeypatch.setattr(engine, 'evaluate', lambda _: state)
    # Simulate interruption after atomic state replacement but before report/events refresh.
    store.save_state(state)
    stale_report = (store.directory / 'report.md').read_text(encoding='utf-8')
    assert 'CUST_CONFIG_ONLY' not in stale_report
    first_handoff = engine.run(store)
    refreshed_report = (store.directory / 'report.md').read_text(encoding='utf-8')
    assert 'CUST_CONFIG_ONLY' in refreshed_report
    initial_events = (store.directory / 'events.jsonl').read_bytes()
    initial_state = (store.directory / 'state.json').read_bytes()
    initial_report = (store.directory / 'report.json').read_bytes()
    engine.run(store)
    assert (store.directory / 'events.jsonl').read_bytes() == initial_events
    assert (store.directory / 'state.json').read_bytes() == initial_state
    assert (store.directory / 'report.json').read_bytes() == initial_report
    assert RunStore.latest(store.root).run_id == store.run_id

    sentinel = 'Bearer ' + '_'.join(['neverpersist', '123456789'])
    with pytest.raises(UnsafeEvidence):
        store.append_event('unsafe', {'note': sentinel})
    contaminated = store.read_state()
    contaminated['source']['note'] = sentinel
    with pytest.raises(UnsafeEvidence):
        store.save_state(contaminated)
    production = store.read_state()
    production['production_ready'] = True
    with pytest.raises(ValueError):
        store.save_state(production)
    approved = store.read_state()
    approved['approved_by'] = 'operator'
    with pytest.raises(ValueError):
        store.save_state(approved)
    with pytest.raises(UnsafeEvidence):
        assert_safe({'compact': sentinel}, compact=True)
    with pytest.raises(UnsafeEvidence):
        store.write_incoming(store.incoming / 'unsafe.json', {'Authorization': sentinel})

    assert len(first_handoff) <= 300
    for name in ('state.json', 'events.jsonl', 'report.json', 'report.md', 'next.txt', 'handoff.txt'):
        assert sentinel not in (store.directory / name).read_text(encoding='utf-8')
    assert sentinel not in json.dumps(compact_status(store.read_state()))
    assert sentinel not in first_handoff
