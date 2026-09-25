"""Private durable run directory, append-only event log, reports, and compact handoff."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import uuid
from typing import Any

from scripts.work_qualification.reasons import GATES, GATE_PHASE, PHASES, reason_detail
from scripts.work_qualification.safety import UnsafeEvidence, assert_safe, assert_safe_patch, canonical_json, sha256_bytes


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def run_id() -> str:
    return f'wq1-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:8]}'


def ensure_private_root(path: Path, repo_root: Path) -> Path:
    if not path.is_absolute():
        raise ValueError('Evidence root must be an absolute path.')
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        pass
    else:
        raise ValueError('Evidence root must be outside the source checkout.')
    resolved.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != 'nt' and (resolved.stat().st_mode & 0o077):
        raise ValueError('Evidence root permissions must be private to the current operator.')
    runs = resolved / 'runs'
    runs.mkdir(mode=0o700, exist_ok=True)
    if os.name != 'nt' and (runs.stat().st_mode & 0o077):
        raise ValueError('Evidence run directory permissions must be private to the current operator.')
    return resolved


def _write_private(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + '.tmp')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name != 'nt':
            os.chmod(path, 0o600)
    finally:
        try: temporary.unlink()
        except FileNotFoundError: pass


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('Qualification run state is missing or invalid.') from error
    if not isinstance(value, dict) or value.get('schema_version') != 1 or not re.fullmatch(r'wq1-\d{8}-[0-9a-f]{8}', str(value.get('run_id', ''))):
        raise ValueError('Qualification run state is missing or invalid.')
    _assert_unapproved(value)
    assert_safe(value)
    return value


def _assert_unapproved(state: dict[str, Any]) -> None:
    if state.get('production_ready') is not False or 'approved_by' in state or 'approved_at' in state:
        raise ValueError('The work qualification harness cannot approve production.')
    if state.get('decision') not in {'QUALIFICATION_INCOMPLETE', 'READY_FOR_OPERATOR_APPROVAL'}:
        raise ValueError('The work qualification decision is invalid.')


class RunStore:
    def __init__(self, root: Path, identifier: str):
        self.root = root
        self.run_id = identifier
        self.directory = root / 'runs' / identifier
        self.incoming = self.directory / 'incoming'
        self.evidence = self.directory / 'evidence'
        self.state_path = self.directory / 'state.json'

    @classmethod
    def create(cls, root: Path, *, source: dict[str, Any]) -> 'RunStore':
        identifier = run_id()
        store = cls(root, identifier)
        store.directory.mkdir(parents=True, mode=0o700)
        store.incoming.mkdir(mode=0o700)
        store.evidence.mkdir(mode=0o700)
        (store.incoming / 'identity-probes').mkdir(mode=0o700)
        (store.incoming / 'references').mkdir(mode=0o700)
        state = {
            'schema_version': 1, 'run_id': identifier, 'created_at': utc_now(),
            'updated_at': utc_now(), 'project': 'react-fastapi-base', 'change': 'CHG-235',
            'request': 'work-env-qualification-harness-v1',
            'target_base_commit': source['target_base_commit'], 'source': source,
            'phases': {phase: {'status': 'NOT_RUN', 'reason_codes': ['ATTENTION_UNKNOWN']} for phase in PHASES},
            'gates': [], 'observations': {}, 'decision': 'QUALIFICATION_INCOMPLETE',
            'production_ready': False,
        }
        assert_safe(state)
        _write_private(store.state_path, canonical_json(state))
        store._write_latest()
        store.append_event('run_created', {'source_digest': source.get('source_digest', '')})
        store.render(state)
        return store

    @classmethod
    def latest(cls, root: Path) -> 'RunStore':
        try:
            latest = json.loads((root / 'latest-run.json').read_text(encoding='utf-8'))
            identifier = latest['run_id']
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError('No resumable qualification run was found in the selected evidence root.') from error
        if not isinstance(identifier, str) or not re.fullmatch(r'wq1-\d{8}-[0-9a-f]{8}', identifier):
            raise ValueError('No resumable qualification run was found in the selected evidence root.')
        store = cls(root, identifier)
        _safe_read_json(store.state_path)
        return store

    def read_state(self) -> dict[str, Any]:
        return _safe_read_json(self.state_path)

    def save_state(self, state: dict[str, Any]) -> None:
        _assert_unapproved(state)
        state['updated_at'] = utc_now()
        assert_safe(state)
        _write_private(self.state_path, canonical_json(state))

    def append_event(self, event_type: str, safe_fields: dict[str, Any]) -> None:
        assert_safe(safe_fields)
        event_file = self.directory / 'events.jsonl'
        prior_hash = '0' * 64
        sequence = 1
        if event_file.exists():
            try:
                lines = event_file.read_text(encoding='utf-8').splitlines()
                if lines:
                    previous = json.loads(lines[-1])
                    prior_hash = previous['event_hash']
                    sequence = int(previous['sequence']) + 1
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                raise ValueError('Qualification event history is invalid.') from None
        body = {'sequence': sequence, 'at': utc_now(), 'event_type': event_type, 'fields': safe_fields, 'previous_hash': prior_hash}
        event_hash = sha256_bytes(canonical_json(body))
        event = {**body, 'event_hash': event_hash}
        assert_safe(event)
        descriptor = os.open(event_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, 'ab') as stream:
            stream.write(canonical_json(event))
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != 'nt': os.chmod(event_file, 0o600)

    def event_fingerprints(self) -> set[str]:
        path = self.directory / 'events.jsonl'
        if not path.is_file(): return set()
        seen: set[str] = set()
        try:
            for line in path.read_text(encoding='utf-8').splitlines():
                event = json.loads(line)
                fingerprint = event.get('fields', {}).get('fingerprint')
                if isinstance(fingerprint, str): seen.add(fingerprint)
        except (OSError, json.JSONDecodeError, AttributeError):
            raise ValueError('Qualification event history is invalid.') from None
        return seen

    def _write_latest(self) -> None:
        _write_private(self.root / 'latest-run.json', canonical_json({'schema_version': 1, 'run_id': self.run_id}))

    def write_evidence(self, name: str, value: Any) -> None:
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{0,79}\.json', name):
            raise ValueError('Evidence artifact name is invalid.')
        assert_safe(value)
        _write_private(self.evidence / name, canonical_json(value))

    def write_incoming(self, path: Path, value: Any) -> None:
        try:
            path.resolve().relative_to(self.incoming.resolve())
        except ValueError:
            raise ValueError('Qualification input path is outside the run directory.') from None
        assert_safe(value)
        _write_private(path, canonical_json(value))

    def write_reference_digest(self, path: Path, digest: str) -> None:
        try:
            path.resolve().relative_to(self.incoming.resolve())
        except ValueError:
            raise ValueError('Qualification input path is outside the run directory.') from None
        if not re.fullmatch(r'evidence-\d{3,4}\.sha256', path.name) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Evidence digest reference is invalid.')
        _write_private(path, (digest + '\n').encode('ascii'))

    def write_evidence_text(self, name: str, value: str) -> None:
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{0,79}\.(?:js|txt|md)', name):
            raise ValueError('Evidence artifact name is invalid.')
        if not isinstance(value, str) or len(value) > 100_000:
            raise ValueError('Evidence artifact is invalid.')
        _write_private(self.evidence / name, value.encode('utf-8'))

    def write_evidence_blob(self, name: str, value: bytes, *, max_bytes: int = 8 * 1024 * 1024) -> None:
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{0,79}\.patch', name) or not isinstance(value, bytes) or len(value) > max_bytes:
            raise ValueError('Evidence patch is invalid.')
        try:
            assert_safe_patch(value.decode('utf-8'))
        except (UnicodeError, UnsafeEvidence):
            raise ValueError('Evidence patch did not match the safe private patch contract.') from None
        _write_private(self.evidence / name, value)

    def render(self, state: dict[str, Any]) -> str:
        _assert_unapproved(state)
        phases = state['phases']
        gates = state['gates']
        report = {
            'schema_version': 1, 'project': state['project'], 'change': state['change'],
            'request': state['request'], 'run_id': state['run_id'], 'created_at': state['created_at'],
            'updated_at': state['updated_at'], 'candidate_version': state['source']['candidate_version'],
            'source': state['source'], 'configuration': state.get('observations', {}).get('configuration', {}),
            'phases': self._expanded_phases(phases), 'company_qualification_gates': gates,
            'customization': phases['customization'], 'decision': state['decision'],
            'production_ready': False,
            'policy': {'external_transport': False, 'operator_approval_required': True, 'source_commit_or_executable_source_binding': state['source']['executable_source_commit'], 'source_digest': state['source']['source_digest']},
        }
        assert_safe(report)
        _write_private(self.directory / 'report.json', canonical_json(report))
        markdown = self._markdown(state)
        _write_private(self.directory / 'report.md', markdown.encode('utf-8'))
        next_text = self._next(state)
        _write_private(self.directory / 'next.txt', next_text.encode('utf-8'))
        bundle = self._inventory()
        handoff = self._handoff(state, bundle['bundle_sha256'])
        assert_safe({'handoff': handoff}, compact=True)
        if len(handoff) > 300:
            raise ValueError('Compact qualification handoff exceeded its fixed length limit.')
        _write_private(self.directory / 'handoff.txt', (handoff + '\n').encode('utf-8'))
        return handoff

    @staticmethod
    def _expanded_phases(phases: dict[str, Any]) -> list[dict[str, Any]]:
        expanded = []
        for phase_id, phase in phases.items():
            reasons = [
                {'code': code, 'explanation': reason_detail(code).explanation, 'next_action': reason_detail(code).next_action}
                for code in phase.get('reason_codes', [])
            ]
            expanded.append({'id': phase_id, **phase, 'reasons': reasons})
        return expanded

    def _markdown(self, state: dict[str, Any]) -> str:
        lines = [
            '# Work-environment qualification report', '',
            f"- Project: `{state['project']}`", f"- Change: `{state['change']}`",
            f"- Candidate: `{state['source']['candidate_version']}`",
            f"- Run: `{state['run_id']}`", f"- Branch: `{state['source'].get('branch', 'unknown')}`",
            f"- Full HEAD: `{state['source'].get('head', 'unknown')}`",
            f"- Executable source commit: `{state['source']['executable_source_commit']}`",
            f"- Executable source digest: `{state['source']['source_digest']}`",
            f"- Target base commit/tree: `{state['source']['target_base_commit']}` / `{state['source'].get('target_base_tree', 'unknown')}`",
            f"- Decision: `{state['decision']}`", '- Production ready: `false`', '',
            '## Phases', '', '| Phase | Status | Reason codes |', '|---|---|---|',
        ]
        for phase_id, phase in state['phases'].items():
            lines.append(f"| `{phase_id}` | **{phase['status']}** | {', '.join(f'`{code}`' for code in phase.get('reason_codes', [])) or '—'} |")
        lines.extend(['', '## Reasons and next actions', ''])
        for phase_id, phase in state['phases'].items():
            for code in phase.get('reason_codes', []):
                detail = reason_detail(code)
                lines.extend([f"### {phase_id}: `{code}`", '', detail.explanation, '', f'Next action: {detail.next_action}', ''])
        lines.extend(['', '## CompanyQualification gates', '', '| Gate | Status | Reason codes |', '|---|---|---|'])
        for gate in state['gates']:
            lines.append(f"| `{gate['id']}` | **{gate['status']}** | {', '.join(f'`{code}`' for code in gate['reason_codes']) or '—'} |")
        paths = state.get('source', {}).get('changed_paths', [])
        path_hashes = state.get('source', {}).get('changed_path_hashes', {})
        lines.extend(['', '## Customization inventory', '', f"Class: `{state['phases']['customization'].get('classification', 'CUST_UNKNOWN')}`; changed paths: {len(paths)}.", ''])
        if paths:
            lines.extend(['| Repository path | SHA-256 |', '|---|---|'])
            for path in paths:
                lines.append(f"| `{path}` | `{path_hashes.get(path, 'unavailable')}` |")
        else:
            lines.append('No changed paths were discovered.')
        local_checks = state.get('observations', {}).get('local_customization_checks', {})
        lines.extend(['', '## Source customization checks', '', f"Private patch: `{local_checks.get('patch_status', 'NOT_RUN')}`; SHA-256: `{local_checks.get('patch_sha256') or 'unavailable'}`.", ''])
        checks = local_checks.get('checks', [])
        if checks:
            lines.extend(['| Check | Status |', '|---|---|'])
            for item in checks:
                lines.append(f"| `{item['check']}` | **{item['status']}** |")
        else:
            lines.append('No local executable-source checks were applicable to the changed paths.')
        lines.extend(['', '## Safe evidence', '', 'Detailed evidence remains in this operator-private run directory. The harness stores allowlisted observations, hashes, and reason codes; it does not transport evidence outward.', ''])
        return '\n'.join(lines)

    def _next(self, state: dict[str, Any]) -> str:
        lines = ['Work-environment qualification next actions', '']
        chain = ('identity', 'tenant_membership', 'storage', 'deployment')
        first_unproven = next((index for index, phase in enumerate(chain) if state['phases'][phase]['status'] != 'PASS'), None)
        allowed_phases = set(PHASES)
        if first_unproven is not None:
            allowed_phases = {'source_identity', 'configuration', 'customization', *chain[:first_unproven + 1]}
        for phase_id, phase in state['phases'].items():
            if phase_id not in allowed_phases: continue
            if phase['status'] == 'PASS': continue
            instruction = phase.get('operator_action_instruction')
            if phase.get('operator_action_state') == 'WAITING_FOR_OPERATOR_ACTION' and isinstance(instruction, str):
                lines.append(f"- [{phase_id}] WAITING_FOR_OPERATOR_ACTION: {instruction}")
                continue
            for code in phase.get('reason_codes', []):
                action = reason_detail(code).next_action
                if action not in lines: lines.append(f'- [{phase_id}/{code}] {action}')
        if state.get('decision') == 'READY_FOR_OPERATOR_APPROVAL':
            lines.extend(['', 'Operator review is still required. Run production preflight and the final two-user smoke with the authorized release workflow.'])
        if state['phases'].get('identity', {}).get('status') == 'PASS' and state['phases'].get('tenant_membership', {}).get('status') != 'PASS':
            lines.extend(['', 'Tenant actions: see evidence/tenant-membership.md. Do not continue until identity/topology pass.'])
        if state['phases'].get('operations', {}).get('operator_action_state') == 'WAITING_FOR_OPERATOR_ACTION':
            lines.extend(['', state['phases']['operations']['operator_action_instruction'], 'See evidence/operations-drills.md for all seven drill steps.'])
        return '\n'.join(lines) + '\n'

    def _inventory(self) -> dict[str, Any]:
        files: dict[str, str] = {}
        for name in ('state.json', 'events.jsonl', 'report.json', 'report.md', 'next.txt'):
            path = self.directory / name
            if path.is_file(): files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(self.evidence.rglob('*')):
            if path.is_file(): files[path.relative_to(self.directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        safe_inputs: list[Path] = []
        for path in sorted(self.incoming.rglob('*.json')):
            try:
                payload = json.loads(path.read_text(encoding='utf-8'))
                assert_safe(payload)
            except (OSError, UnicodeError, json.JSONDecodeError, UnsafeEvidence):
                continue
            safe_inputs.append(path)
        for index, path in enumerate(safe_inputs, start=1):
            files[f'input/observation-{index:04d}'] = hashlib.sha256(path.read_bytes()).hexdigest()
        references = []
        for path in sorted(self.incoming.rglob('evidence-*.sha256')):
            try:
                value = path.read_text(encoding='ascii').strip()
                if not re.fullmatch(r'[0-9a-f]{64}', value): continue
                references.append(path)
            except (OSError, UnicodeError):
                continue
        for index, path in enumerate(references, start=1):
            files[f'input/reference-{index:04d}'] = hashlib.sha256(path.read_bytes()).hexdigest()
        encoded = json.dumps(files, sort_keys=True, separators=(',', ':')).encode('utf-8')
        inventory = {'schema_version': 1, 'files': files, 'bundle_sha256': hashlib.sha256(encoded).hexdigest(), 'handoff_excluded': True}
        assert_safe(inventory)
        _write_private(self.directory / 'inventory.json', canonical_json(inventory))
        return inventory

    def _handoff(self, state: dict[str, Any], bundle_sha: str) -> str:
        source = state['source']
        version = str(source['candidate_version'])
        match = re.fullmatch(r'.*-rc\.(\d+)', version)
        version_label = f'rc{match.group(1)}' if match else version
        deployment = state.get('observations', {}).get('configuration', {}).get('deployment_hash')
        dep = deployment[:8] if isinstance(deployment, str) and re.fullmatch(r'[0-9a-f]{64}', deployment) else 'unknown0'
        abbreviated = {'technical_release': 'TR', 'identity': 'ID', 'storage': 'ST', 'deployment': 'DEP', 'ui_accessibility': 'UI', 'performance': 'PF', 'operations': 'OP', 'release_evidence': 'RE'}
        aliases = {
            'CFG_NOT_QUALIFICATION': 'NOT_QUAL', 'CFG_PROFILE_NOT_COMPANY': 'PROFILE',
            'CFG_DATA_ROOT_INVALID': 'DATA_ROOT', 'CFG_DEPLOYMENT_ID_MISSING': 'DEPLOY_ID',
            'CFG_ORIGIN_OR_HOST_INVALID': 'ORIGIN', 'CFG_CSRF_INVALID': 'CSRF',
            'CFG_SCANNER_REQUIRED_MISSING': 'SCANNER', 'CFG_QUALIFICATION_PREREQS_MISSING': 'PREREQ',
            'CFG_PREFLIGHT_FAIL': 'PREFLIGHT', 'CFG_READINESS_FAIL': 'READY',
            'CFG_DOCS_EXPOSED': 'DOCS',
            'SRC_EXACT': 'EXACT', 'SRC_OLD_BUILD': 'OLD', 'SRC_HEAD_MISMATCH': 'HEAD',
            'SRC_DIRTY_WORKTREE': 'DIRTY', 'SRC_RELEASE_IDENTITY_MISMATCH': 'IDENTITY',
            'SRC_API_INCOMPATIBLE': 'API', 'SRC_UNKNOWN_DEPLOYED_BUILD': 'BUILD',
            'ID_MISSING': 'MISSING', 'ID_SAME_USER': 'SAME_USER', 'ID_USER_UNSTABLE': 'UNSTABLE',
            'ID_SHARED_INSTANCE': 'SHARED_INSTANCE', 'ID_DEPLOYMENT_MISMATCH': 'DEPLOYMENT',
            'ID_PROFILE_MISMATCH': 'PROFILE', 'ID_TOPOLOGY_UNPROVEN': 'TOPOLOGY',
            'ID_CROSS_USER_ROUTING_UNPROVEN': 'ROUTING', 'ID_AFTER_RESTART_MISMATCH': 'RESTART',
            'ID_SHARED_PROCESS_ACCESSKEY': 'SHARED_KEY', 'ST_PROVIDER_SUPPORT_MISSING': 'SUPPORT',
            'ST_KIND_UNSUPPORTED': 'KIND', 'ST_MULTI_HOST_UNSUPPORTED': 'MULTIHOST',
            'ST_ROOT_MISMATCH': 'ROOT', 'ST_DOCTOR_FAIL': 'DOCTOR', 'ST_RESTART_LOSS': 'RESTART',
            'ST_REDEPLOY_LOSS': 'REDEPLOY', 'ST_BACKUP_FAIL': 'BACKUP', 'ST_RESTORE_FAIL': 'RESTORE',
            'ST_ATTACHMENT_MISMATCH': 'ATTACH', 'DEP_HEALTH_FAIL': 'HEALTH',
            'DEP_READINESS_FAIL': 'READY', 'DEP_FRONTEND_BACKEND_MISMATCH': 'FRONTEND',
            'DEP_HTTPS_FAIL': 'HTTPS', 'DEP_INGRESS_AUTH_UNPROVEN': 'INGRESS',
            'DEP_UNAUTHENTICATED_ACCESS': 'UNAUTH', 'DEP_REDEPLOY_FAIL': 'REDEPLOY',
            'DEP_ROLLBACK_FAIL': 'ROLLBACK', 'UI_BROWSER_FAIL': 'BROWSER',
            'UI_PERMISSION_STATE_FAIL': 'PERMISSION', 'UI_KEYBOARD_FAIL': 'KEYBOARD',
            'UI_A11Y_AUTOMATION_FAIL': 'A11Y', 'UI_REFLOW_FAIL': 'REFLOW',
            'UI_NATIVE_ASSISTIVE_BLOCKED': 'NATIVE', 'PERF_REPOSITORY_FAIL': 'REPO',
            'PERF_COMPANY_OBSERVATION_MISSING': 'MISSING', 'PERF_THRESHOLD_FAIL': 'THRESHOLD',
            'ATTENTION_UNKNOWN': 'UNKNOWN', 'QUAL_GATES_BLOCKED': 'BLOCKED',
        }
        drill_aliases = {
            'STARTUP_RESTART': 'START', 'DEPENDENCY_UNAVAILABLE_RECOVERY': 'DEPS',
            'DATABASE_READINESS_DEGRADATION': 'DB', 'WORKER_CRASH_LEASE_RECOVERY': 'WORKER',
            'OUTBOUND_INTEGRATION_FAILURE_RETRY': 'OUT', 'RECOVERY_RESTORE': 'RESTORE',
            'REQUEST_LOG_CORRELATION': 'CORR',
        }
        def code_alias(code: str) -> str:
            if code.startswith('OPS_'):
                parts = code.split('_')
                drill = '_'.join(parts[1:-1])
                state_code = parts[-1]
                return f"{drill_aliases.get(drill, 'OPS')}:{state_code[:1]}"
            return aliases.get(code, 'UNKNOWN')

        entries = []
        for gate in state['gates']:
            if gate['status'] == 'PASS': continue
            candidates = [code for code in gate['reason_codes'] if code != 'ATTENTION_UNKNOWN']
            primary = candidates[0] if candidates else (gate['reason_codes'][0] if gate['reason_codes'] else 'ATTENTION_UNKNOWN')
            grade = 'F' if gate['status'] == 'FAIL' else 'B'
            entries.append(f"{abbreviated[gate['id']]}:{grade}:{code_alias(primary)}")
        if state['decision'] == 'READY_FOR_OPERATOR_APPROVAL':
            outcome = 'READY_FOR_OPERATOR_APPROVAL'; entries = []
        elif any(item['status'] == 'FAIL' for item in state['gates']): outcome = 'FAIL'
        else: outcome = 'ATTN'
        cust = state['phases']['customization'].get('classification', 'CUST_UNKNOWN')
        suffix = f"run={state['run_id'][-8:]} bundle={bundle_sha[:12]}"
        prefix = f"RFBWQ1 v={version_label} src={source['source_digest'][:8]} dep={dep} result={outcome}"
        pieces = [prefix, 'gates=' + ','.join(entries), 'cust=' + cust, suffix]
        handoff = ' '.join(pieces)
        if len(handoff) > 300:
            handoff = f"RFBWQ1 v={version_label} src={source['source_digest'][:8]} dep={dep} result={outcome} gates=TR:B:UNKNOWN,ID:B:UNKNOWN,ST:B:UNKNOWN,DEP:B:UNKNOWN,UI:B:UNKNOWN,PF:B:UNKNOWN,OP:B:UNKNOWN,RE:B:UNKNOWN cust={cust[:24]} {suffix}"
        return handoff


def compact_status(state: dict[str, Any]) -> dict[str, Any]:
    phase_statuses = {phase: value['status'] for phase, value in state['phases'].items()}
    return {
        'run_id': state['run_id'], 'candidate_version': state['source']['candidate_version'],
        'decision': state['decision'], 'production_ready': False,
        'phase_statuses': phase_statuses,
        'blocked_gates': [gate['id'] for gate in state['gates'] if gate['status'] != 'PASS'],
    }
