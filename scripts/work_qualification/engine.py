"""Discovery and orchestration for the resumable work qualification phases."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from scripts.release_version import current_release_paths, parse_candidate_version
from scripts.work_qualification.assess import (
    assess_customization, assess_deployment, assess_identity, assess_performance,
    assess_storage, assess_tenant, assess_ui, final_qualification, load_identity_probes, phase_result, validate_operations,
)
from scripts.work_qualification.reasons import PHASES, REASONS, reason_detail
from scripts.work_qualification.safety import UnsafeEvidence, assert_safe, assert_safe_patch, canonical_json, safe_text_hash, sha256_bytes
from scripts.work_qualification.source import ROOT, configuration_observations, repository_identity, safe_url_origin
from scripts.work_qualification.store import RunStore, utc_now


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _request_json(url: str) -> tuple[int, dict[str, Any] | None]:
    try:
        response = build_opener(_NoRedirect).open(Request(url, headers={'Accept': 'application/json', 'Cache-Control': 'no-store'}), timeout=8)
        status = response.status
        body = response.read(65537)
        if len(body) > 65536:
            return status, None
        payload = json.loads(body.decode('utf-8'))
        return status, payload if isinstance(payload, dict) else None
    except HTTPError as error:
        # Do not inspect an error body or its URL.
        return int(error.code), None
    except (URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return 0, None


def _request_status(url: str) -> int:
    """Probe only the status; never read a documentation or OpenAPI body."""
    try:
        response = build_opener(_NoRedirect).open(Request(url, headers={'Accept': 'application/json', 'Cache-Control': 'no-store'}), timeout=8)
        status = int(response.status)
        response.close()
        return status
    except HTTPError as error:
        return int(error.code)
    except (URLError, TimeoutError, OSError, ValueError):
        return 0


def deployed_observations() -> dict[str, Any] | None:
    frontend_value = os.environ.get('BASE_WORK_QUALIFICATION_FRONTEND_ORIGIN', '')
    backend_value = os.environ.get('BASE_WORK_QUALIFICATION_BACKEND_ORIGIN', '')
    if not frontend_value and not backend_value:
        return None
    front = safe_url_origin(frontend_value) if frontend_value else None
    back = safe_url_origin(backend_value) if backend_value else None
    result: dict[str, Any] = {
        'frontend_origin_hash': front[0] if front else None,
        'frontend_https': front is not None and front[1] == 'https',
        'backend_origin_hash': back[0] if back else None,
        'backend_https': back is not None and back[1] == 'https',
        'runtime_config_status': 0, 'runtime_api_base_hash': None,
        'runtime_api_matches_backend': False, 'health_status': 0,
        'health_ok': False, 'backend_build_version': None,
        'readiness_status': 0, 'readiness_ok': False,
        'unauthenticated_identity_status': 0,
        'unauthenticated_identity_refused': False,
        'docs_status': 0, 'openapi_status': 0,
        'deployment_hash': None,
    }
    if not front and not back:
        return result
    if front:
        code, runtime = _request_json(frontend_value.rstrip('/') + '/runtime-config.json')
        result['runtime_config_status'] = code
        api_base = runtime.get('apiBase') if runtime and runtime.get('schemaVersion') == 1 else None
        runtime_origin = safe_url_origin(api_base) if isinstance(api_base, str) and api_base else None
        if runtime_origin:
            result['runtime_api_base_hash'] = runtime_origin[0]
            result['runtime_api_matches_backend'] = bool(back and runtime_origin[0] == back[0])
            result['runtime_api_https'] = runtime_origin[1] == 'https'
    if back:
        health_code, health = _request_json(backend_value.rstrip('/') + '/api/v1/health')
        result['health_status'] = health_code
        result['health_ok'] = health_code == 200 and bool(health and health.get('alive') is True)
        if health:
            value = health.get('version')
            if isinstance(value, str):
                try:
                    result['backend_build_version'] = parse_candidate_version(value).version
                except ValueError:
                    pass
        ready_code, ready = _request_json(backend_value.rstrip('/') + '/api/v1/readiness')
        result['readiness_status'] = ready_code
        result['readiness_ok'] = ready_code == 200 and bool(ready and ready.get('ready') is True)
        proof_code, _ = _request_json(backend_value.rstrip('/') + '/api/v1/identity-proof')
        result['unauthenticated_identity_status'] = proof_code
        result['unauthenticated_identity_refused'] = proof_code in (401, 403)
        result['docs_status'] = _request_status(backend_value.rstrip('/') + '/docs')
        result['openapi_status'] = _request_status(backend_value.rstrip('/') + '/openapi.json')
        result['docs_exposed'] = result['docs_status'] == 200 or result['openapi_status'] == 200
    assert_safe(result)
    return result


def _preflight_status(environment: str) -> bool | None:
    if environment not in {'qualification', 'production'}:
        return None
    venv_python = ROOT / 'backend/.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    python = str(venv_python) if venv_python.is_file() else sys.executable
    try:
        result = subprocess.run(
            [python, '-m', 'app.cli', 'preflight'], cwd=ROOT / 'backend',
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=30, check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _typed_prerequisites(config: dict[str, Any]) -> dict[str, Any] | None:
    path = os.environ.get('BASE_QUALIFICATION_PREREQUISITES_FILE', '')
    if not path:
        return None
    try:
        sys.path.insert(0, str(ROOT / 'backend'))
        from app.platform.settings import CompanyQualificationPrerequisites
        item = CompanyQualificationPrerequisites.model_validate_json(Path(path).read_text(encoding='utf-8'))
        configured_deployment = os.environ.get('BASE_DEPLOYMENT_ID', '')
        configured_root = os.environ.get('BASE_DATA_ROOT', '')
        try:
            from pathlib import Path as _Path
            exact_root = bool(configured_root and _Path(item.persistent_root).resolve() == _Path(configured_root).resolve())
        except (OSError, RuntimeError, ValueError):
            exact_root = False
        deployment_matches = item.deployment_id == configured_deployment
        reference_hash = safe_text_hash(item.provider_sqlite_support_reference)
        return {
            'valid': True, 'deployment_matches': deployment_matches, 'root_binding_exact': exact_root,
            'identity_topology': item.identity_topology, 'storage_kind': item.storage_kind,
            'provider_reference': item.provider_sqlite_support_reference,
            'provider_reference_hash': reference_hash,
            'all_clients_same_host': item.all_database_clients_same_host is True,
            'authorization_present': bool(item.authorized_by and item.authorized_at),
        }
    except Exception:
        # Model errors may include attacker-controlled fragments. Keep no exception detail.
        return None


def _doctor_storage() -> bool | None:
    scratch = os.environ.get('BASE_WORK_QUALIFICATION_SCRATCH_PARENT', '')
    if not scratch:
        return None
    try:
        path = Path(scratch).expanduser()
        if not path.is_absolute() or not path.is_dir():
            return False
        venv_python = ROOT / 'backend/.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        python = str(venv_python) if venv_python.is_file() else sys.executable
        result = subprocess.run(
            [python, '-m', 'app.cli', 'doctor-storage', '--scratch-parent', str(path)],
            cwd=ROOT / 'backend', stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=90, check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _repository_perf_pass(source: dict[str, Any]) -> bool | None:
    path = ROOT / 'evidence/current/performance/qualification.json'
    try:
        report = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        report.get('candidate_version') != source['candidate_version']
        or report.get('source_commit') != source['executable_source_commit']
        or report.get('source_digest') != source['source_digest']
    ):
        return None
    return report.get('overall_status') == 'PASS'


def _repository_verification(source: dict[str, Any]) -> dict[str, bool]:
    path = ROOT / 'evidence/current/full-stack/verification.json'
    try:
        report = json.loads(path.read_text(encoding='utf-8'))
        verified = bool(
            report.get('code_ready') is True and report.get('exit_code') == 0
            and report.get('source_commit') == source['executable_source_commit']
            and report.get('source_digest') == source['source_digest']
        )
    except (OSError, json.JSONDecodeError):
        verified = False
    paths = current_release_paths(ROOT)
    release_files = all(item.is_file() for item in (paths.identity, paths.manifest, paths.evidence_binding, paths.readiness_matrix))
    return {'technical_release_pass': verified, 'release_evidence_pass': verified and release_files}


def _repository_ui_status(source: dict[str, Any]) -> bool | None:
    path = ROOT / 'evidence/current/full-stack/verification.json'
    try:
        report = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    if report.get('source_commit') != source['executable_source_commit'] or report.get('source_digest') != source['source_digest']:
        return None
    required = {'frontend-typecheck', 'frontend-unit', 'frontend-build', 'browser-e2e-accessibility', 'ui-state-matrix-results'}
    rows = {row.get('name'): row.get('status') for row in report.get('results', []) if isinstance(row, dict)}
    if any(rows.get(name) == 'FAIL' for name in required):
        return False
    if report.get('code_ready') is not True or any(rows.get(name) != 'PASS' for name in required):
        return None
    return True


def _local_check_environment(temporary: Path) -> dict[str, str]:
    # Subprocesses receive only execution essentials. In particular, provider
    # credentials, identity variables, proxy settings, and user package config
    # do not cross this boundary.
    environment = {
        key: os.environ[key]
        for key in ('PATH', 'SYSTEMROOT', 'WINDIR', 'LANG', 'LC_ALL')
        if key in os.environ
    }
    environment['HOME'] = str(temporary / 'home')
    (temporary / 'home').mkdir(mode=0o700, exist_ok=True)
    environment.update({'TMPDIR': str(temporary), 'TEMP': str(temporary), 'TMP': str(temporary), 'PYTHONHASHSEED': '0', 'TZ': 'UTC'})
    environment.update({
        'BASE_ENVIRONMENT': 'test', 'BASE_PROFILE': 'development',
        'BASE_DEV_USER': 'work-qualification.local',
        'BASE_DATA_ROOT': str(temporary / 'data'),
        'BASE_ALLOWED_ORIGINS': json.dumps(['http://127.0.0.1']),
        'BASE_ALLOWED_HOSTS': json.dumps(['127.0.0.1']),
        'BASE_CSRF_SECRET': 'work-qualification-test-only-csrf-seed-0000000000000000',
        'BASE_ATTACHMENT_UPLOAD_MODE': 'disabled',
    })
    return environment


def _run_local_check(name: str, command: list[str], *, cwd: Path, environment: dict[str, str], timeout: int = 300) -> dict[str, str]:
    try:
        result = subprocess.run(
            command, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {'check': name, 'status': 'BLOCKED'}
    if result.returncode == 0:
        status = 'PASS'
    elif 'ModuleNotFoundError' in result.stdout or 'No module named' in result.stdout:
        status = 'BLOCKED'
    else:
        status = 'FAIL'
    return {'check': name, 'status': status}


def _private_change_patch(source: dict[str, Any]) -> bytes | None:
    if source.get('sensitive_path_risk') is True or any(any(marker in path.casefold() for marker in ('.env', 'secret', 'credential', 'key.pem')) for path in source.get('changed_paths', [])):
        raise UnsafeEvidence('Source patch has a secret-risk path.')
    tracked = subprocess.run(
        ['git', 'diff', '--binary', source['target_base_commit'], '--'],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if tracked.returncode:
        return None
    pieces = [tracked.stdout]
    untracked = subprocess.run(
        ['git', 'ls-files', '--others', '--exclude-standard', '-z'],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if untracked.returncode:
        return None
    for raw_path in filter(None, untracked.stdout.split(b'\x00')):
        try:
            relative = raw_path.decode('utf-8')
        except UnicodeDecodeError:
            return None
        if any(character in relative for character in ('\n', '\r', '\x00')):
            return None
        if any(marker in relative.casefold() for marker in ('.env', 'secret', 'credential', 'key.pem')):
            raise UnsafeEvidence('Source patch has a secret-risk path.')
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            continue
        added = subprocess.run(
            ['git', 'diff', '--binary', '--no-index', '--', os.devnull, relative],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if added.returncode not in (0, 1):
            return None
        if added.stdout:
            pieces.append(added.stdout)
    patch = b''.join(pieces)
    if len(patch) > 8 * 1024 * 1024:
        return None
    try:
        assert_safe_patch(patch.decode('utf-8'))
    except (UnicodeError, UnsafeEvidence):
        raise UnsafeEvidence('Source patch contains secret-like or non-text content.') from None
    return patch


def _source_local_checks(store: RunStore, source: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    paths = source.get('changed_paths', [])
    source_paths = [path for path in paths if path == 'dev' or path.startswith((
        'backend/', 'frontend/', 'scripts/', 'tests/', 'contracts/', 'experience-lab/', 'catalog/',
    ))]
    if not source_paths:
        return {'status': 'NOT_RUN', 'source_digest': source['source_digest'], 'checks': [], 'patch_status': 'NOT_RUN', 'patch_sha256': None}
    prior = previous if previous and previous.get('source_digest') == source['source_digest'] else None
    prior_patch = store.evidence / 'customization.patch'
    if prior and prior.get('status') in {'PASS', 'FAIL'} and prior.get('patch_status') in {'PASS', 'FAIL'} and prior_patch.is_file():
        return prior
    if source.get('sensitive_path_risk') is True or any(any(marker in path.casefold() for marker in ('.env', 'secret', 'credential', 'key.pem')) for path in source_paths):
        return {
            'status': 'FAIL', 'source_digest': source['source_digest'], 'checks': [],
            'patch_status': 'FAIL', 'patch_sha256': None,
        }

    checks: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix='work-qualification-check-') as temporary_name:
        temporary = Path(temporary_name)
        environment = _local_check_environment(temporary)
        if any(path.startswith(('backend/app/', 'backend/tests/', 'backend/pyproject.toml')) for path in source_paths):
            junit = temporary / 'backend-junit.xml'
            checks.append(_run_local_check(
                'backend-tests', [sys.executable, 'scripts/backend_test_runner.py', '--output', str(junit)],
                cwd=ROOT, environment=environment, timeout=600,
            ))
        if any(path.startswith(('scripts/', 'tests/')) or path == 'dev' for path in source_paths):
            checks.append(_run_local_check(
                'tooling-tests', [sys.executable, '-m', 'pytest', '-q', 'tests'],
                cwd=ROOT, environment=environment, timeout=600,
            ))
        if any(path.startswith('contracts/') for path in source_paths):
            checks.append(_run_local_check(
                'contracts', [sys.executable, 'dev', 'contracts'],
                cwd=ROOT, environment=environment, timeout=300,
            ))
        if any(path.startswith(('backend/app/platform/', 'frontend/src/platform/')) for path in source_paths):
            checks.append(_run_local_check(
                'architecture', [sys.executable, 'scripts/check_architecture.py'],
                cwd=ROOT, environment=environment, timeout=120,
            ))
        if any(path.startswith(('frontend/', 'experience-lab/src/')) for path in source_paths):
            if not (ROOT / 'frontend/node_modules').is_dir():
                checks.extend({'check': name, 'status': 'BLOCKED'} for name in ('frontend-typecheck', 'frontend-unit', 'frontend-build'))
            else:
                checks.extend([
                    _run_local_check('frontend-typecheck', ['npm', 'run', 'typecheck'], cwd=ROOT / 'frontend', environment=environment, timeout=300),
                    _run_local_check('frontend-unit', ['npm', 'test'], cwd=ROOT / 'frontend', environment=environment, timeout=300),
                    _run_local_check('frontend-build', ['npm', 'run', 'build'], cwd=ROOT / 'frontend', environment=environment, timeout=600),
                ])
        if any(path.startswith('experience-lab/src/') for path in source_paths):
            checks.append(_run_local_check(
                'experience-lab-build', [sys.executable, 'dev', 'lab-build'],
                cwd=ROOT, environment=environment, timeout=300,
            ))
            checks.append(_run_local_check(
                'experience-lab-tests', [sys.executable, 'dev', 'test-lab', '--mode', 'in_memory'],
                cwd=ROOT, environment=environment, timeout=300,
            ))

    statuses = {check['status'] for check in checks}
    status = 'FAIL' if 'FAIL' in statuses else ('BLOCKED' if 'BLOCKED' in statuses else 'PASS')
    patch_status = 'BLOCKED'
    patch_sha256 = None
    try:
        patch = _private_change_patch(source)
        if patch is not None:
            store.write_evidence_blob('customization.patch', patch)
            patch_status = 'PASS'
            patch_sha256 = hashlib.sha256(patch).hexdigest()
    except UnsafeEvidence:
        status = 'FAIL'
        patch_status = 'FAIL'
    except (OSError, ValueError):
        patch_status = 'BLOCKED'
    if patch_status != 'PASS' and status == 'PASS':
        status = 'BLOCKED'
    return {
        'status': status, 'source_digest': source['source_digest'],
        'checks': checks, 'patch_status': patch_status, 'patch_sha256': patch_sha256,
    }


def _template(phase: str, binding: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    return {'schema_version': 1, 'phase': phase, 'binding': binding, 'facts': facts}


def _ensure_forms(store: RunStore, binding: dict[str, Any]) -> None:
    forms = {
        'tenant.json': ('tenant_membership', {
            'action': 'unknown', 'dedicated_non_demo': None,
            'existing_operator_commands_used': None, 'migration_result': 'unknown',
            'maintenance_acknowledged': None,
        }),
        'storage.json': ('storage', {
            'storage_kind': None, 'provider_reference_verified': None, 'all_clients_same_host': None,
            'root_binding_exact': None, 'restart_persistent': None, 'redeploy_persistent': None,
            'backup_pass': None, 'restore_new_root_pass': None, 'attachment_enabled': None,
            'restore_target_is_new_empty': None, 'original_root_preserved': None,
            'original_attachment_sha256': None, 'restored_attachment_sha256': None,
            'host_replacement': 'unknown',
        }),
        'deployment.json': ('deployment', {
            'health_ok': None, 'readiness_ok': None,
            'frontend_backend_independent': None, 'runtime_api_binding': None, 'https': None,
            'ingress_authentication': None, 'unauthenticated_refused': None,
            'restart_redeploy_stable': None, 'rolling_compatibility': None,
            'rollback_recovery': None, 'deployment_stable': None, 'api_compatible': None,
            'deployed_source_commit_matches': None, 'deployed_source_digest_matches': None,
        }),
        'ui.json': ('ui_accessibility', {
            'major_workflows': None, 'role_permission_states': None, 'keyboard_focus': None,
            'semantic_accessibility': None, 'light_dark_high_contrast': None, 'reduced_motion': None,
            'zoom_reflow': None, 'width_320': None, 'width_390': None,
            'native_assistive_technology': None,
        }),
        'performance.json': ('performance', {
            'route_classes': None, 'sample_count': None, 'p95_latency_ms': None, 'threshold_ms': None,
            'bounded_read_only_sampling': None, 'large_data_path': None,
            'ag_grid_virtualization': None, 'environment_class': None,
        }),
    }
    for name, (phase, facts) in forms.items():
        path = store.incoming / name
        if not path.exists() or _replace_untouched_template(path, phase, facts, binding):
            store.write_incoming(path, _template(phase, binding, facts))
        reference_dir = store.incoming / 'references' / phase
        reference_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    topology_path = store.incoming / 'identity-topology.json'
    topology_facts = {
        'schema_version': 1, 'binding': binding, 'topology': 'unknown',
        'cross_user_routing_refused': None, 'simultaneous_users_confirmed': None,
        'provider_evidence_type': 'unknown', 'provider_evidence_reference': '',
        'provider_document_checked': None,
    }
    if not topology_path.exists() or _replace_untouched_template(topology_path, 'identity-topology', topology_facts, binding, topology=True):
        store.write_incoming(topology_path, topology_facts)
    (store.incoming / 'references' / 'identity').mkdir(parents=True, mode=0o700, exist_ok=True)
    operations_guide = store.evidence / 'operations-drills.md'
    if not operations_guide.exists():
        store.write_evidence_text('operations-drills.md', _operations_guide())
    tenant_guide = store.evidence / 'tenant-membership.md'
    if not tenant_guide.exists():
        store.write_evidence_text('tenant-membership.md', _tenant_action_guide())
    probe_source = Path(__file__).with_name('browser_probe.js')
    if probe_source.is_file():
        store.write_evidence_text('browser-probe.js', probe_source.read_text(encoding='utf-8'))
    operations_path = store.incoming / 'company-operations-evidence.json'
    if not operations_path.exists():
        try:
            template = json.loads((ROOT / 'deploy/company-operations-evidence.template.json').read_text(encoding='utf-8'))
            template.update({
                'deployment_id': os.environ.get('BASE_DEPLOYMENT_ID') or None,
                'candidate_version': binding['candidate_version'],
                'verified_source_commit': binding['source_commit'],
                'source_digest': binding['source_digest'],
                'created_at': utc_now(),
            })
            store.write_incoming(operations_path, template)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            # The operations phase remains blocked if a safe typed template cannot be made.
            pass


def _replace_untouched_template(path: Path, phase: str, defaults: dict[str, Any], binding: dict[str, Any], *, topology: bool = False) -> bool:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return False
    if topology:
        unchanged = value == defaults | {'binding': value.get('binding')}
    else:
        unchanged = value == _template(phase, value.get('binding'), defaults)
    return unchanged and value.get('binding') != binding


def _operations_guide() -> str:
    return '''# Company operations drills\n\nRecord each result in `incoming/company-operations-evidence.json` using the existing typed model. Do not include request bodies, headers, stack traces, secrets, or private hostnames. Use safe correlation IDs and timezone timestamps.\n\n| Drill | Preparation and expected observation | Actor |\n|---|---|---|\n| `startup_restart` | Record healthy liveness/readiness; cleanly stop and restart the qualification service; verify the same deployment binding and data. | Provider/operator restarts; harness checks health/readiness. |\n| `dependency_unavailable_recovery` | In an approved disposable qualification setup, make one declared dependency unavailable, observe bounded degraded readiness, restore it, then verify recovery. | Provider/operator controls the dependency; harness does not inject faults. |\n| `database_readiness_degradation` | Use the approved database fault procedure; verify readiness reports unavailable while the database is down and recovers after restoration. Never use a live database. | Provider/operator controls the database; harness probes readiness. |\n| `worker_crash_lease_recovery` | Dispatch a safe deterministic job, stop the worker before acknowledgement using the provider's normal control, and verify lease recovery/fencing with no duplicate external side effect. | Provider/operator controls the worker; harness does not create jobs. |\n| `outbound_integration_failure_retry` | Point only at an approved test endpoint, fail one bounded request, restore the endpoint, and verify maintained retry/idempotency behavior. | Provider/operator controls the endpoint; harness sends no outbound test traffic. |\n| `recovery_restore` | Follow the existing maintenance restore procedure into a new empty root; preserve the original root and compare database/object/attachment evidence including original attachment SHA-256. | Operator restores under APP-STOPPED; harness validates typed evidence. |\n| `request_log_correlation` | Make a harmless request and verify its safe correlation ID in the approved request and application logs; record no body or headers. | Operator checks provider logs; harness stores only a hash of the correlation ID. |\n\nProvider-specific controls must use the provider's documented interface. The harness does not invent provider commands or perform disruptive actions. Resume with `./dev work-qualify --resume` after adding sanitized evidence.\n'''


def _tenant_action_guide() -> str:
    return '''# Qualification tenant and membership

Proceed only after phase 2 identity and provider topology pass. Reuse a dedicated qualification tenant when its two real users already have the required roles. Otherwise use the repository operator CLI against the explicitly selected qualification deployment: `python -m app.cli provision --tenant <dedicated-name> --admin <User-A-id>`, then `python -m app.cli add-member --tenant-id <returned-id> --user <User-B-id> --role viewer` (or `editor`). Use `python -m app.cli migrate --maintenance APP-STOPPED` only when migration is required and the operator has stopped every application and worker process. Never use demo seed.

Do not run these commands from a workstation that is not bound to the intended qualification database. Do not put user IDs or tenant names in the harness form. Record only whether the existing commands were used, whether the tenant is dedicated/non-demo and migration outcome in `incoming/tenant.json`; store supporting source evidence with `./dev work-qualify --reference tenant_membership /absolute/path/to/operator-record`. Collect fresh interleaved browser observations and verify roles/permissions from bootstrap.
'''


def _source_reason(source: dict[str, Any], deployed: dict[str, Any] | None, deployment: dict[str, Any]) -> list[str]:
    codes = list(source['reason_codes'])
    version = source['candidate_version']
    deployed_version = deployed.get('backend_build_version') if deployed else None
    if not deployed_version:
        codes.append('SRC_UNKNOWN_DEPLOYED_BUILD')
    else:
        try:
            if parse_candidate_version(deployed_version).version != version:
                codes.append('SRC_OLD_BUILD')
        except ValueError:
            codes.append('SRC_UNKNOWN_DEPLOYED_BUILD')
    deployment_codes = set(deployment.get('reason_codes', []))
    if 'SRC_HEAD_MISMATCH' in deployment_codes:
        codes.append('SRC_HEAD_MISMATCH')
    return sorted(set(codes))


def _require_prior_pass(result: dict[str, Any], prerequisites: tuple[str, ...], phases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    missing = [phase for phase in prerequisites if phases[phase].get('status') != 'PASS']
    if not missing or result.get('status') != 'PASS':
        return result
    reasons = sorted({code for phase in missing for code in phases[phase].get('reason_codes', [])}) or ['ATTENTION_UNKNOWN']
    return phase_result('BLOCKED', reasons, {
        'blocked_by_phases': missing,
        'operator_action_state': 'WAITING_FOR_OPERATOR_ACTION',
        'operator_action_instruction': f"Complete the earliest blocked prerequisite phase ({missing[0]}) before using this evidence.",
    })


def evaluate(store: RunStore) -> dict[str, Any]:
    state = store.read_state()
    source = repository_identity()
    if source['target_base_commit'] != state['target_base_commit']:
        raise ValueError('Qualification run is bound to another target base.')
    config = configuration_observations()
    preflight = _preflight_status(config['environment'])
    if preflight is False and config['environment'] in {'qualification', 'production'}:
        config['reason_codes'] = sorted(set(config['reason_codes'] + ['CFG_PREFLIGHT_FAIL']))
        config['status'] = 'FAIL'
    deployed = deployed_observations()
    if deployed and not deployed.get('readiness_ok'):
        config['reason_codes'] = sorted(set(config['reason_codes'] + ['CFG_READINESS_FAIL']))
        config['status'] = 'FAIL'
    prereqs = _typed_prerequisites(config)
    if config['environment'] == 'qualification' and (
        prereqs is None or prereqs.get('deployment_matches') is not True
        or prereqs.get('root_binding_exact') is not True
        or prereqs.get('authorization_present') is not True
    ):
        config['reason_codes'] = sorted(set(config['reason_codes'] + ['CFG_QUALIFICATION_PREREQS_MISSING']))
        config['status'] = 'FAIL'
    if deployed and config.get('docs_exposure_expected_disabled') and deployed.get('docs_exposed') is True:
        config['reason_codes'] = sorted(set(config['reason_codes'] + ['CFG_DOCS_EXPOSED']))
        config['status'] = 'FAIL'
    preliminary_probes = load_identity_probes(store.incoming / 'identity-probes')
    binding_deployment_hash = config.get('deployment_hash') or (preliminary_probes[0]['deployment_hash'] if preliminary_probes else None)
    binding = {
        'candidate_version': source['candidate_version'],
        'source_commit': source['executable_source_commit'],
        'source_digest': source['source_digest'],
        'deployment_hash': binding_deployment_hash,
    }
    _ensure_forms(store, binding)
    identity = assess_identity(
        store.incoming / 'identity-probes',
        expected_api_major=source['api']['frontend_major'] or 1,
        expected_api_revision=source['api']['frontend_revision'] or 1,
        expected_binding=binding,
    )
    tenant = assess_tenant(identity, store.incoming, binding)
    doctor = _doctor_storage()
    storage = assess_storage(store.incoming, binding, prereqs, doctor)
    storage = _require_prior_pass(storage, ('identity', 'tenant_membership'), {'identity': identity, 'tenant_membership': tenant})
    network_for_deployment = None
    if deployed:
        front_hash = deployed.get('frontend_origin_hash')
        back_hash = deployed.get('backend_origin_hash')
        network_for_deployment = {
            'health_ok': deployed.get('health_ok') is True,
            'readiness_ok': deployed.get('readiness_ok') is True,
            'frontend_backend_independent': bool(front_hash and back_hash and front_hash != back_hash),
            'runtime_api_binding': deployed.get('runtime_api_matches_backend') is True,
            'https': deployed.get('frontend_https') is True and deployed.get('backend_https') is True and deployed.get('runtime_api_https') is True,
            'unauthenticated_refused': deployed.get('unauthenticated_identity_refused') is True,
            'api_compatible': identity.get('api_compatible') is True,
            'docs_exposure_disabled': deployed.get('docs_exposed') is False,
        }
    deployment = assess_deployment(store.incoming, binding, network_for_deployment)
    if config['reason_codes']:
        deployment = {
            **deployment,
            'status': 'FAIL' if deployment.get('status') == 'FAIL' or (
                config.get('environment') in {'qualification', 'production'}
                and any(code in {'CFG_PREFLIGHT_FAIL', 'CFG_READINESS_FAIL', 'CFG_DOCS_EXPOSED', 'CFG_CSRF_INVALID', 'CFG_SCANNER_REQUIRED_MISSING'} for code in config['reason_codes'])
            ) else 'BLOCKED',
            'reason_codes': sorted(set(deployment.get('reason_codes', []) + config['reason_codes'])),
        }
    deployment = _require_prior_pass(deployment, ('identity', 'tenant_membership', 'storage'), {
        'identity': identity, 'tenant_membership': tenant, 'storage': storage,
    })
    ui = assess_ui(store.incoming, binding, _repository_ui_status(source))
    ui = _require_prior_pass(ui, ('identity', 'tenant_membership', 'storage', 'deployment'), {
        'identity': identity, 'tenant_membership': tenant, 'storage': storage, 'deployment': deployment,
    })
    repository_perf = _repository_perf_pass(source)
    performance = assess_performance(store.incoming, binding, repository_perf)
    performance = _require_prior_pass(performance, ('identity', 'tenant_membership', 'storage', 'deployment'), {
        'identity': identity, 'tenant_membership': tenant, 'storage': storage, 'deployment': deployment,
    })
    deployment_id = os.environ.get('BASE_DEPLOYMENT_ID') or None
    operations = validate_operations(
        store.incoming / 'company-operations-evidence.json',
        version=source['candidate_version'], source_commit=source['executable_source_commit'],
        source_digest=source['source_digest'], deployment_id=deployment_id,
    )
    if operations.get('status') in {'BLOCKED', 'FAIL'}:
        operations['operator_action_state'] = 'WAITING_FOR_OPERATOR_ACTION'
        operations['operator_action_instruction'] = (
            'Complete the exact seven drills in evidence/operations-drills.md using approved provider controls, '
            'then add sanitized typed evidence and resume.'
        )
    operations = _require_prior_pass(operations, ('identity', 'tenant_membership', 'storage', 'deployment'), {
        'identity': identity, 'tenant_membership': tenant, 'storage': storage, 'deployment': deployment,
    })
    local_checks = _source_local_checks(store, source, state.get('observations', {}).get('local_customization_checks'))
    architecture_row = next((item for item in local_checks['checks'] if item['check'] == 'architecture'), None)
    architecture_pass = None if architecture_row is None else architecture_row['status'] == 'PASS'
    customization = assess_customization(source, architecture_pass=architecture_pass)
    customization['architecture_check_status'] = 'NOT_RUN' if architecture_row is None else architecture_row['status']
    customization['local_checks'] = local_checks['checks']
    customization['private_patch_status'] = local_checks['patch_status']
    customization['private_patch_sha256'] = local_checks['patch_sha256']
    if local_checks['status'] == 'FAIL' and (local_checks['checks'] or local_checks['patch_status'] == 'FAIL'):
        customization['status'] = 'FAIL'
    elif local_checks['status'] == 'BLOCKED':
        customization['status'] = 'BLOCKED'
    if customization.get('classification') in {'CUST_SOURCE_REVERIFY_REQUIRED', 'CUST_SUPPORTED', 'CUST_API_REVISION_REQUIRED'}:
        if local_checks['status'] == 'FAIL':
            customization['status'] = 'FAIL'
            customization['reason_codes'] = [customization['classification']]
        elif local_checks['status'] == 'BLOCKED':
            customization['status'] = 'BLOCKED'
            customization['reason_codes'] = [customization['classification']]
    verification = _repository_verification(source)
    source['technical_release_pass'] = verification['technical_release_pass']
    source['release_evidence_pass'] = verification['release_evidence_pass']
    source_codes = _source_reason(source, deployed, deployment)
    source_codes.extend(code for code in identity.get('reason_codes', []) if code == 'SRC_API_INCOMPATIBLE')
    identity_build = identity.get('deployed_build_version')
    if identity_build and not (deployed and deployed.get('backend_build_version')):
        source_codes = [code for code in source_codes if code != 'SRC_UNKNOWN_DEPLOYED_BUILD']
        try:
            if parse_candidate_version(identity_build).version != source['candidate_version']:
                source_codes.append('SRC_OLD_BUILD')
        except ValueError:
            source_codes.append('SRC_UNKNOWN_DEPLOYED_BUILD')
        source_codes = sorted(set(source_codes))
    elif not (deployed and deployed.get('backend_build_version')):
        source_codes.append('SRC_UNKNOWN_DEPLOYED_BUILD')
    if not verification['technical_release_pass']:
        source_codes.append('SRC_RELEASE_IDENTITY_MISMATCH')
    source_codes = sorted(set(source_codes))
    dirty_only = all(code in {'SRC_DIRTY_WORKTREE', 'SRC_RELEASE_IDENTITY_MISMATCH', 'SRC_UNKNOWN_DEPLOYED_BUILD', 'SRC_OLD_BUILD'} for code in source_codes)
    if 'SRC_HEAD_MISMATCH' in source_codes or 'SRC_API_INCOMPATIBLE' in source_codes:
        source_status = 'FAIL'
    elif source_codes == ['SRC_EXACT']:
        source_status = 'PASS'
    elif dirty_only and source['changed_paths']:
        source_status = 'ATTENTION'
    else:
        source_status = 'BLOCKED'
    if not source_codes: source_codes = ['SRC_EXACT']
    phase_map = {
        'source_identity': {'status': source_status, 'reason_codes': source_codes, **verification,
                            'deployed_build_version': (deployed.get('backend_build_version') if deployed else None) or identity_build},
        'configuration': {'status': 'PASS' if not config['reason_codes'] else 'BLOCKED', 'reason_codes': config['reason_codes'] or [],
                          'preflight_pass': preflight is True, 'readiness_observed': bool(deployed)},
        'identity': identity, 'tenant_membership': tenant, 'storage': storage,
        'deployment': deployment, 'ui_accessibility': ui, 'performance': performance,
        'operations': operations, 'customization': customization,
    }
    qualification, gates = final_qualification(phase_map)
    phase_map['final_qualification'] = qualification
    for result in phase_map.values():
        if result.get('status') != 'PASS' and result.get('reason_codes'):
            result.setdefault('operator_action_state', 'WAITING_FOR_OPERATOR_ACTION')
            primary = next((code for code in result['reason_codes'] if code != 'ATTENTION_UNKNOWN'), result['reason_codes'][0])
            result.setdefault('operator_action_instruction', reason_detail(primary).next_action)
    state['source'] = source
    state['observations'] = {
        'configuration': config, 'deployed': deployed or {'observed': False},
        'prerequisites': {key: value for key, value in (prereqs or {}).items() if key not in {'provider_reference'}},
        'preflight_pass': preflight, 'local_customization_checks': local_checks,
    }
    if not config.get('deployment_hash') and binding_deployment_hash:
        state['observations']['configuration']['deployment_hash'] = binding_deployment_hash
    state['phases'] = phase_map
    state['gates'] = gates
    state['decision'] = qualification['decision']
    state['production_ready'] = False
    assert_safe(state)
    return state


def run(store: RunStore) -> str:
    before = store.read_state()
    state = evaluate(store)
    before_compare = {key: value for key, value in before.items() if key != 'updated_at'}
    state_compare = {key: value for key, value in state.items() if key != 'updated_at'}
    if state_compare != before_compare:
        store.save_state(state)
    else:
        state = before
    seen = store.event_fingerprints()
    probes = load_identity_probes(store.incoming / 'identity-probes')
    if probes:
        for item in probes:
            safe_observation = {key: item[key] for key in (
                'label', 'captured_at', 'user_hash', 'instance_hash', 'deployment_hash',
                'tenant_hash', 'role', 'profile', 'identity_source',
            )}
            fingerprint = sha256_bytes(canonical_json(safe_observation))
            if fingerprint not in seen:
                event_type = 'lifecycle_observation' if item['label'] in {'A3', 'B3'} else 'identity_observation'
                store.append_event(event_type, {**safe_observation, 'fingerprint': fingerprint})
                seen.add(fingerprint)
    for phase_id in ('storage', 'deployment', 'ui_accessibility', 'performance'):
        phase = state['phases'][phase_id]
        evidence_digest = phase.get('evidence_digest')
        if phase.get('evidence_count', 0) and isinstance(evidence_digest, str):
            safe_observation = {'phase': phase_id, 'evidence_digest': evidence_digest, 'status': phase['status']}
            fingerprint = sha256_bytes(canonical_json(safe_observation))
            if fingerprint not in seen:
                store.append_event('phase_evidence_observation', {**safe_observation, 'fingerprint': fingerprint})
                seen.add(fingerprint)
    operations = state['phases']['operations']
    if operations.get('typed_model_valid'):
        safe_observation = {'drills': operations['drills']}
        fingerprint = sha256_bytes(canonical_json(safe_observation))
        if fingerprint not in seen:
            store.append_event('operations_observation', {**safe_observation, 'fingerprint': fingerprint})
    evaluation_fields = {
        'source_digest': state['source']['source_digest'],
        'phase_statuses': {phase: state['phases'][phase]['status'] for phase in PHASES},
        'decision': state['decision'],
    }
    evaluation_fingerprint = sha256_bytes(canonical_json(evaluation_fields))
    if evaluation_fingerprint not in seen:
        store.append_event('phase_evaluation', {**evaluation_fields, 'fingerprint': evaluation_fingerprint})
    handoff = store.render(state)
    return handoff
