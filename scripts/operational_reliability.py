#!/usr/bin/env python3
"""Run the deterministic source-bound repository operational qualification."""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import tempfile
import time
from typing import Any, Iterator
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts.operational_diagnostics import safe_diagnostics_summary
from scripts.operational_reliability_contract import (
    EXTERNAL_DRILL_IDS,
    REPOSITORY_SCENARIO_IDS,
    contract_hash,
    load_contract,
)
from scripts.source_manifest import checkout_commit, executable_source_commit, source_digest
from scripts.release_version import parse_candidate_version

from app.main import create_app
from app.platform import events, jobs, webhooks
from app.platform.attachments import AttachmentUpload, attach
from app.platform.backup import restore, sha256, snapshot
from app.platform.database import Database
from app.platform.errors import AppError
from app.platform.models import Attachment, DurableJob, WebhookDelivery, WebhookEndpoint
from app.platform.security import Actor
from app.platform.settings import Settings
from app.platform.storage import MemoryStorage
from app.platform.provision import provision
from app.platform.version import VERSION
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError


_FULL_SHA = re.compile(r'^[0-9a-f]{40}$')
_DIGEST = re.compile(r'^[0-9a-f]{64}$')
_FORBIDDEN_KEYS = {
    'accesskey', 'authorization', 'cookie', 'credential', 'credentials',
    'password', 'raw_qualification_payload', 'request_body', 'secret',
    'secret_fingerprint', 'stack_trace', 'private_filesystem_root',
}


class QualificationFailure(AssertionError):
    """A deterministic repository scenario did not produce its safe outcome."""


class Fixture:
    def __init__(self, work: Path, settings: Settings, database: Database, tenant: str, client: TestClient):
        self.work = work
        self.settings = settings
        self.database = database
        self.tenant = tenant
        self.client = client


@contextmanager
def disposable_fixture(*, webhook_allowed_hosts: list[str] | None = None) -> Iterator[Fixture]:
    with tempfile.TemporaryDirectory(prefix='base-operations-') as temporary:
        work = Path(temporary)
        settings = Settings(
            environment='test',
            profile='development',
            data_root=work / 'data',
            dev_user='alice',
            request_limit_per_minute=1000,
            webhook_allowed_hosts=webhook_allowed_hosts or [],
        )
        seed_database = Database(settings)
        tenant = provision(seed_database, 'Operations qualification', 'alice')
        seed_database.close()
        app = create_app(settings)
        with TestClient(app) as client:
            bootstrap = client.get('/api/v1/bootstrap')
            if bootstrap.status_code != 200:
                raise QualificationFailure('development bootstrap was not available')
            client.headers.update({'X-Tenant-Id': tenant, 'X-CSRF-Token': bootstrap.json()['csrf_token']})
            yield Fixture(work, settings, app.state.database, tenant, client)


def _create_item(fixture: Fixture) -> dict[str, Any]:
    response = fixture.client.post('/api/v1/work-items', json={'title': 'Operational qualification item'})
    if response.status_code != 201:
        raise QualificationFailure('disposable work item could not be created')
    return response.json()


def _actor(fixture: Fixture) -> Actor:
    return Actor('alice', fixture.tenant, 'admin', 'operations-qualification', frozenset({'read', 'write', 'admin', 'restore'}))


def _attachment_payload(filename: str = 'operations.txt', content: bytes = b'bounded operations content') -> AttachmentUpload:
    return AttachmentUpload(filename=filename, content_type='text/plain', content_base64=base64.b64encode(content).decode('ascii'))


def _scenario_startup_invalid_profile() -> str:
    from app.platform.configuration_contract import ConfigurationContractError
    settings = Settings(environment='production', profile='development', data_root=Path('unsafe-relative-root'))
    with patch('app.main.load_profile') as load_profile:
        try:
            create_app(settings)
        except ConfigurationContractError:
            pass
        else:
            raise QualificationFailure('invalid production-like configuration was accepted')
        if load_profile.called:
            raise QualificationFailure('profile runtime was constructed before configuration refusal')
    return 'startup refused before profile-owned runtime construction'


def _scenario_no_development_fallback() -> str:
    from app.platform.configuration_contract import ConfigurationContractError
    settings = Settings(environment='production', profile='development', data_root=Path('relative'))
    try:
        settings.assert_configuration()
    except ConfigurationContractError as error:
        if 'company profile' not in str(error).casefold():
            raise QualificationFailure('configuration refusal did not identify the profile contract')
    else:
        raise QualificationFailure('production-like development profile was accepted')
    return 'development identity and runtime fallback were refused'


def _scenario_readiness_dependency_unavailable() -> str:
    with disposable_fixture() as fixture:
        health = fixture.client.get('/api/v1/health')
        tenant_database = fixture.database.path(fixture.tenant)
        tenant_database.unlink()
        readiness = fixture.client.get('/api/v1/readiness')
        if health.status_code != 200 or health.json().get('alive') is not True:
            raise QualificationFailure('liveness did not remain available')
        if readiness.status_code != 503 or readiness.json() != {'ready': False, 'code': 'configuration_or_database_unready'}:
            raise QualificationFailure('readiness did not fail closed with its bounded response')
        if tenant_database.exists():
            raise QualificationFailure('readiness recreated a missing tenant database')
    return 'liveness stayed alive while missing dependency readiness returned bounded 503'


def _scenario_database_safe_503() -> str:
    with disposable_fixture() as fixture:
        sensitive_sql = 'SELECT credential FROM /private/provider/root'

        def fail_session(*_args: Any, **_kwargs: Any):
            raise OperationalError(sensitive_sql, {}, RuntimeError('credential=do-not-disclose'))

        fixture.database.session = fail_session  # type: ignore[method-assign]
        response = fixture.client.get('/api/v1/work-items')
        payload = response.json()
        encoded = response.text
        if response.status_code != 503 or payload.get('error', {}).get('code') != 'database_busy':
            raise QualificationFailure('database failure did not use the safe 503 envelope')
        if not response.headers.get('x-request-id') or payload['error'].get('request_id') != response.headers['x-request-id']:
            raise QualificationFailure('database failure lost request correlation')
        if any(value in encoded for value in (sensitive_sql, 'credential=do-not-disclose', '/private/provider/root', 'OperationalError')):
            raise QualificationFailure('database failure leaked provider details')
    return 'database failure produced correlated bounded 503 without provider detail leakage'


def _scenario_attachment_scanner_failure() -> str:
    with disposable_fixture() as fixture:
        item = _create_item(fixture)

        class FailingScanner:
            def scan(self, *_args: Any, **_kwargs: Any) -> bool:
                raise RuntimeError('scanner provider detail')

        storage = MemoryStorage()
        with fixture.database.session(fixture.tenant) as session:
            try:
                attach(
                    session,
                    _actor(fixture),
                    'work_items',
                    item['id'],
                    _attachment_payload(),
                    tenant_id=fixture.tenant,
                    storage=storage,
                    scanner=FailingScanner(),
                    upload_mode='scanner_required',
                    registry=fixture.client.app.state.entities,
                )
            except AppError as error:
                if error.status != 503 or error.code != 'scanner_unavailable':
                    raise QualificationFailure('scanner failure used the wrong safe reason')
            else:
                raise QualificationFailure('scanner failure was accepted')
            if session.query(Attachment).count() != 0:
                raise QualificationFailure('scanner failure left an attachment row')
            session.rollback()
        if storage._objects:
            raise QualificationFailure('scanner failure left object residue')
    return 'scanner failure failed closed without row or object residue'


def _scenario_attachment_storage_failure() -> str:
    with disposable_fixture() as fixture:
        item = _create_item(fixture)

        class PartialStorage(MemoryStorage):
            def put(self, tenant_id: str, key: str, content: bytes, content_type: str):
                stored = super().put(tenant_id, key, content, content_type)
                raise RuntimeError(f'provider failed after {stored.size} bytes')

        storage = PartialStorage()
        with fixture.database.session(fixture.tenant) as session:
            try:
                attach(
                    session,
                    _actor(fixture),
                    'work_items',
                    item['id'],
                    _attachment_payload(),
                    tenant_id=fixture.tenant,
                    storage=storage,
                    scanner=None,
                    upload_mode='trusted_types',
                    registry=fixture.client.app.state.entities,
                )
            except AppError as error:
                if error.status != 503 or error.code != 'storage_unavailable':
                    raise QualificationFailure('storage failure used the wrong safe reason')
            else:
                raise QualificationFailure('storage failure was accepted')
            if session.query(Attachment).count() != 0:
                raise QualificationFailure('storage failure left an attachment row')
            session.rollback()
        if storage._objects:
            raise QualificationFailure('storage failure left object residue')
    return 'storage failure ran compensating cleanup without row or object residue'


def _scenario_job_behaviour() -> str:
    with disposable_fixture() as fixture:
        actor = _actor(fixture)
        with fixture.database.session(fixture.tenant) as session:
            queued = jobs.enqueue(session, actor, 'operations.always-fails', {}, max_attempts=2)
            session.commit()
            job_id = queued.id

        def fail(_payload: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError('handler failure detail')

        first = jobs.process_one(fixture.database, fixture.tenant, 'worker-a', {'operations.always-fails': fail}, lease_seconds=5, heartbeat_interval=.02)
        if first is None or first.status != 'retrying' or first.attempts != 1:
            raise QualificationFailure('handler failure did not schedule bounded retry')
        delay = first.run_after.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
        if delay.total_seconds() <= 0 or delay.total_seconds() > 3:
            raise QualificationFailure('retry delay exceeded its bounded policy')
        with fixture.database.session(fixture.tenant) as session:
            row = session.get(DurableJob, job_id)
            row.run_after = datetime.now(timezone.utc) - timedelta(seconds=1)
            session.commit()
        second = jobs.process_one(fixture.database, fixture.tenant, 'worker-a', {'operations.always-fails': fail}, lease_seconds=5, heartbeat_interval=.02)
        if second is None or second.status != 'failed' or second.attempts != 2:
            raise QualificationFailure('final handler failure was not recorded at max attempts')

        with fixture.database.session(fixture.tenant) as session:
            heartbeat_job = jobs.enqueue(session, actor, 'operations.heartbeat', {})
            session.commit()
            heartbeat_id = heartbeat_job.id

        def long_handler(_payload: dict[str, Any]) -> dict[str, Any]:
            time.sleep(.18)
            with fixture.database.session(fixture.tenant) as session:
                if jobs.lease_next(session, 'worker-b', lease_seconds=1) is not None:
                    raise QualificationFailure('live job lease was reclaimed despite heartbeat')
            return {'heartbeat': True}

        heartbeat_result = jobs.process_one(fixture.database, fixture.tenant, 'worker-a', {'operations.heartbeat': long_handler}, lease_seconds=1, heartbeat_interval=.02)
        if heartbeat_result is None or heartbeat_result.id != heartbeat_id or heartbeat_result.status != 'succeeded':
            raise QualificationFailure('lease heartbeat did not preserve the live worker')

        with fixture.database.session(fixture.tenant) as session:
            fenced_job = jobs.enqueue(session, actor, 'operations.fenced', {})
            session.commit()
            fenced_id = fenced_job.id

        def stale_handler(_payload: dict[str, Any]) -> dict[str, Any]:
            with fixture.database.session(fixture.tenant) as session:
                current = session.get(DurableJob, fenced_id)
                current.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
                session.commit()
            with fixture.database.session(fixture.tenant) as session:
                replacement = jobs.lease_next(session, 'worker-b', lease_seconds=5)
                if replacement is None or replacement.id != fenced_id:
                    raise QualificationFailure('reclaim worker did not obtain the expired lease')
                session.commit()
            return {'stale': True}

        fenced_result = jobs.process_one(fixture.database, fixture.tenant, 'worker-a', {'operations.fenced': stale_handler}, lease_seconds=5, heartbeat_interval=.02)
        if fenced_result is None or fenced_result.status != 'running' or fenced_result.lease_owner != 'worker-b':
            raise QualificationFailure('stale worker finalized after losing its fence')
    return 'retry, final failure, heartbeat, reclaim and stale-fence protection all held'


def _scenario_webhooks() -> str:
    with disposable_fixture(webhook_allowed_hosts=['hooks.example.com']) as fixture:
        settings = fixture.settings
        os.environ['BASE_WEBHOOK_SECRET_OPERATIONS'] = 's' * 40
        try:
            for unsafe in ('http://hooks.example.com/events', 'https://127.0.0.1/events'):
                try:
                    webhooks.validate_url(unsafe, settings)
                except AppError:
                    pass
                else:
                    raise QualificationFailure('unsafe webhook destination was accepted')
            try:
                webhooks.secret_for('MISSING_OPERATIONS_SECRET', settings)
            except AppError as error:
                if error.code != 'webhook_secret_unavailable':
                    raise QualificationFailure('missing webhook secret used the wrong safe reason')
            else:
                raise QualificationFailure('missing webhook secret was accepted')

            actor = _actor(fixture)
            with fixture.database.session(fixture.tenant) as session:
                endpoint = WebhookEndpoint(
                    id='operations-webhook',
                    name='Operations webhook',
                    url='https://hooks.example.com/events',
                    topics=['operations.failure'],
                    secret_ref='OPERATIONS',
                    enabled=True,
                    revision=1,
                    created_by='alice',
                )
                session.add(endpoint)
                event = events.emit(session, actor, 'operations.failure', {'sensitive': 'payload-not-returned'})
                session.commit()
                event_id = event.event_id

            class Response:
                def __init__(self, status_code: int):
                    self.status_code = status_code

            class Client:
                def __init__(self, status_code: int | None = None):
                    self.status_code = status_code
                    self.calls: list[tuple[str, bytes, dict[str, str]]] = []

                def post(self, url: str, content: bytes, headers: dict[str, str]):
                    self.calls.append((url, content, headers))
                    if self.status_code is None:
                        raise OSError('network provider detail')
                    return Response(self.status_code)

            for status_code, reason, expected_error in ((503, 'non_success_response', 'non_success_response'), (302, 'redirect_refused', 'non_success_response'), (None, 'network_failure', 'delivery_failed')):
                fake = Client(status_code)
                with fixture.database.session(fixture.tenant) as session:
                    try:
                        webhooks.deliver(session, settings, endpoint.id, event_id, client=fake)
                    except RuntimeError:
                        pass
                    else:
                        raise QualificationFailure('webhook failure was accepted as delivered')
                    session.commit()
                    delivery = session.scalar(select(WebhookDelivery).where(WebhookDelivery.endpoint_id == endpoint.id, WebhookDelivery.event_id == event_id))
                    if delivery is None or delivery.status != 'retrying' or delivery.last_error != expected_error:
                        raise QualificationFailure(f'webhook {reason} did not remain durably retryable')
                    if status_code is not None and delivery.response_summary != f'HTTP {status_code}':
                        raise QualificationFailure('webhook response summary was not bounded')
                    if 's' * 20 in json.dumps(delivery.__dict__, default=str) or 'sensitive' in json.dumps(delivery.__dict__, default=str):
                        raise QualificationFailure('webhook delivery state leaked sensitive material')
            if 'follow_redirects=False' not in (ROOT / 'backend/app/platform/webhooks.py').read_text(encoding='utf-8'):
                raise QualificationFailure('webhook redirects are not explicitly disabled')
        finally:
            os.environ.pop('BASE_WEBHOOK_SECRET_OPERATIONS', None)
    return 'unsafe destinations and secrets refused; non-2xx and redirect responses remained durable retries'


def _scenario_recovery() -> str:
    with disposable_fixture() as fixture:
        item = _create_item(fixture)
        upload = fixture.client.post(
            f"/api/v1/work-items/{item['id']}/attachments",
            json={
                'filename': 'recovery.txt',
                'content_type': 'text/plain',
                'content_base64': base64.b64encode(b'recovery qualification bytes').decode('ascii'),
            },
        )
        if upload.status_code != 201:
            raise QualificationFailure('recovery attachment fixture could not be created')
        live_hashes = {str(path.relative_to(fixture.database.root)): sha256(path) for path in fixture.database.root.rglob('*.sqlite3')}
        snapshot_root = snapshot(fixture.database.root, fixture.work / 'snapshot', maintenance='APP-STOPPED')
        manifest_path = snapshot_root / 'manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        (snapshot_root / manifest['databases'][0]['path']).write_bytes(b'corrupt')
        try:
            restore(snapshot_root, fixture.work / 'restore-corrupt')
        except ValueError:
            pass
        else:
            raise QualificationFailure('corrupt snapshot was restored')
        if (fixture.work / 'restore-corrupt').exists():
            raise QualificationFailure('corrupt restore published a target')
        if live_hashes != {str(path.relative_to(fixture.database.root)): sha256(path) for path in fixture.database.root.rglob('*.sqlite3')}:
            raise QualificationFailure('corrupt restore mutated live data')

        clean_snapshot = snapshot(fixture.database.root, fixture.work / 'snapshot-clean', maintenance='APP-STOPPED')
        clean_manifest_path = clean_snapshot / 'manifest.json'
        clean_manifest = json.loads(clean_manifest_path.read_text(encoding='utf-8'))
        clean_manifest['databases'][0]['path'] = '../unsafe.sqlite3'
        clean_manifest_path.write_text(json.dumps(clean_manifest), encoding='utf-8')
        try:
            restore(clean_snapshot, fixture.work / 'restore-traversal')
        except ValueError:
            pass
        else:
            raise QualificationFailure('traversal snapshot was restored')
        if (fixture.work / 'restore-traversal').exists():
            raise QualificationFailure('traversal restore published a target')
    return 'corrupt and traversal-unsafe snapshots were refused without target publication or live mutation'


def _scenario_diagnostics() -> str:
    sensitive = 'do-not-serialize-secret'
    report = {
        'candidate_version': VERSION,
        'candidate_head': 'a' * 40,
        'executable_source_commit': 'b' * 40,
        'source_digest': 'c' * 64,
        'contract_id': 'react-fastapi-base.operational-reliability',
        'contract_revision': 1,
        'contract_sha256': 'd' * 64,
        'repository_operations_status': 'PASS',
        'company_operations_status': 'BLOCKED_EXTERNAL',
        'scenario_results': [{'id': 'OR-DIAGNOSTICS-SAFE-REDACTION', 'status': 'PASS', 'reason_code': 'diagnostic_redacted', 'secret': sensitive}],
        'external_blockers': [{'id': 'request_log_correlation', 'status': 'BLOCKED_EXTERNAL', 'reason_code': 'company_staging_required', 'private_filesystem_root': '/private'}],
        'raw_qualification_payload': sensitive,
    }
    summary = safe_diagnostics_summary(report)
    serialized = json.dumps(summary, sort_keys=True)
    if sensitive in serialized or '/private' in serialized or 'raw_qualification_payload' in serialized:
        raise QualificationFailure('safe diagnostics serialized sensitive evidence fields')
    if set(summary) != {
        'report_type', 'candidate_version', 'candidate_head', 'executable_source_commit', 'source_digest',
        'contract_id', 'contract_revision', 'contract_sha256', 'repository_operations_status',
        'company_operations_status', 'production_ready', 'scenario_statuses', 'external_blockers',
    }:
        raise QualificationFailure('safe diagnostics returned an unmaintained field')
    return 'diagnostics exposed only sanitized source, scenario and blocker metadata'


_SCENARIO_FUNCTIONS = {
    'OR-STARTUP-INVALID-PROFILE': _scenario_startup_invalid_profile,
    'OR-STARTUP-NO-DEV-FALLBACK': _scenario_no_development_fallback,
    'OR-READINESS-DEPENDENCY-UNAVAILABLE': _scenario_readiness_dependency_unavailable,
    'OR-DATABASE-SAFE-503': _scenario_database_safe_503,
    'OR-ATTACHMENT-SCANNER-FAIL-CLOSED': _scenario_attachment_scanner_failure,
    'OR-ATTACHMENT-STORAGE-FAIL-CLOSED': _scenario_attachment_storage_failure,
    'OR-JOB-BOUNDED-RETRY': _scenario_job_behaviour,
    'OR-JOB-HEARTBEAT': _scenario_job_behaviour,
    'OR-JOB-FENCE-RECLAIM': _scenario_job_behaviour,
    'OR-WEBHOOK-UNSAFE-DESTINATION': _scenario_webhooks,
    'OR-WEBHOOK-DURABLE-RETRY': _scenario_webhooks,
    'OR-RECOVERY-INVALID-SNAPSHOT': _scenario_recovery,
    'OR-DIAGNOSTICS-SAFE-REDACTION': _scenario_diagnostics,
}


def _contract_rows(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row['id']: row for row in contract['repository_scenarios']}


def _safe_report_key_check(value: Any, *, top_level: bool = True) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).casefold()
            if normalized in _FORBIDDEN_KEYS or (normalized == 'production_ready' and not top_level):
                return False
            if not _safe_report_key_check(child, top_level=False):
                return False
    elif isinstance(value, list):
        return all(_safe_report_key_check(child, top_level=False) for child in value)
    return True


def validate_report(report: dict[str, Any], *, expected_provenance: dict[str, str] | None = None, contract: dict[str, Any] | None = None) -> list[str]:
    contract = load_contract() if contract is None else contract
    expected_provenance = expected_provenance or {
        'checkout_commit': checkout_commit(ROOT),
        'executable_source_commit': executable_source_commit(ROOT),
        'source_digest': source_digest(),
    }
    errors: list[str] = []
    if report.get('schema_version') != 1 or report.get('report_type') != 'repository-operational-reliability-qualification':
        errors.append('report_identity_invalid')
    if report.get('contract_id') != contract['contract_id'] or report.get('contract_revision') != contract['contract_revision'] or report.get('contract_sha256') != contract_hash(contract):
        errors.append('contract_mismatch')
    if report.get('candidate_version') != VERSION or report.get('candidate_version') != parse_candidate_version(VERSION).version:
        errors.append('version_mismatch')
    if report.get('executable_source_commit') != expected_provenance['executable_source_commit'] or report.get('source_digest') != expected_provenance['source_digest']:
        errors.append('source_mismatch')
    candidate_head = str(report.get('candidate_head', ''))
    if not _FULL_SHA.fullmatch(candidate_head):
        errors.append('candidate_head_invalid')
    elif candidate_head != expected_provenance['checkout_commit']:
        check = __import__('subprocess').run(['git', 'merge-base', '--is-ancestor', candidate_head, expected_provenance['checkout_commit']], cwd=ROOT, check=False)
        if check.returncode != 0:
            errors.append('candidate_checkout_stale')
    ids = tuple(row.get('id') for row in report.get('scenario_results', []) if isinstance(row, dict))
    if ids != REPOSITORY_SCENARIO_IDS:
        errors.append('required_scenario_missing_or_reordered')
    if len(report.get('scenario_results', [])) != len(REPOSITORY_SCENARIO_IDS):
        errors.append('required_scenario_count_invalid')
    for row in report.get('scenario_results', []):
        if not isinstance(row, dict) or row.get('status') != 'PASS' or not row.get('reason_code') or not row.get('safe_outcome'):
            errors.append('scenario_not_passed_or_sanitized')
    blockers = report.get('external_blockers')
    blocker_ids = tuple(row.get('id') for row in blockers if isinstance(row, dict)) if isinstance(blockers, list) else ()
    if blocker_ids != EXTERNAL_DRILL_IDS or any(row.get('status') != 'BLOCKED_EXTERNAL' or row.get('reason_code') != 'company_staging_required' for row in blockers if isinstance(row, dict)):
        errors.append('external_blockers_invalid')
    if report.get('repository_operations_status') != 'PASS' or report.get('company_operations_status') != 'BLOCKED_EXTERNAL' or report.get('production_ready') is not False or report.get('release_status') != 'NOT_CERTIFIED':
        errors.append('production_claim_or_operations_status_invalid')
    if not _safe_report_key_check(report):
        errors.append('sensitive_evidence_field_present')
    created_at = report.get('created_at')
    try:
        parsed = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed > datetime.now(timezone.utc):
            errors.append('evidence_timestamp_invalid')
    except ValueError:
        errors.append('evidence_timestamp_invalid')
    return sorted(set(errors))


def qualify(output: Path) -> dict[str, Any]:
    contract = load_contract()
    rows = _contract_rows(contract)
    provenance = {
        'checkout_commit': checkout_commit(ROOT),
        'executable_source_commit': executable_source_commit(ROOT),
        'source_digest': source_digest(),
    }
    scenario_results: list[dict[str, Any]] = []
    for scenario_id in REPOSITORY_SCENARIO_IDS:
        row = rows[scenario_id]
        function = _SCENARIO_FUNCTIONS.get(scenario_id)
        status = 'PASS'
        reason_code = row['reason_codes'][0]
        safe_outcome = row['expected_safe_outcome']
        if function is None:
            status = 'FAIL'
            reason_code = 'required_scenario_not_implemented'
            safe_outcome = 'required scenario is not implemented by the maintained harness'
        else:
            try:
                observed = function()
                safe_outcome = observed
                reason_code = 'scenario_passed'
            except Exception:
                status = 'FAIL'
                reason_code = 'scenario_failed'
        scenario_results.append({'id': scenario_id, 'status': status, 'reason_code': reason_code, 'safe_outcome': safe_outcome})
        print(f'{status:7} {scenario_id}', flush=True)

    report: dict[str, Any] = {
        'schema_version': 1,
        'report_type': 'repository-operational-reliability-qualification',
        'contract_id': contract['contract_id'],
        'contract_revision': contract['contract_revision'],
        'contract_sha256': contract_hash(contract),
        'candidate_version': VERSION,
        'candidate_head': provenance['checkout_commit'],
        'executable_source_commit': provenance['executable_source_commit'],
        'source_digest': provenance['source_digest'],
        'created_at': datetime.now(timezone.utc).isoformat(),
        'environment': {
            'kind': 'repository_test',
            'profile': 'development',
            'runner': 'disposable_local_resources',
            'python': platform.python_version(),
            'platform': platform.system(),
        },
        'scenario_results': scenario_results,
        'repository_operations_status': 'PASS' if all(row['status'] == 'PASS' for row in scenario_results) else 'FAIL',
        'external_blockers': [
            {
                'id': row['id'],
                'status': 'BLOCKED_EXTERNAL',
                'reason_code': 'company_staging_required',
                'safe_outcome': 'authentic company-profile staging evidence is required for this drill category',
            }
            for row in contract['external_drill_categories']
        ],
        'company_operations_status': 'BLOCKED_EXTERNAL',
        'production_ready': False,
        'release_status': 'NOT_CERTIFIED',
        'note': 'Repository operations PASS is source-bound software evidence only and cannot set the CompanyQualification operations or overall gate to PASS.',
    }
    validation_errors = validate_report(report, expected_provenance=provenance, contract=contract)
    if validation_errors:
        report['repository_operations_status'] = 'FAIL'
        report['validation_errors'] = validation_errors
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/operations/qualification.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        try:
            report = json.loads(args.output.read_text(encoding='utf-8'))
            errors = validate_report(report)
        except (OSError, json.JSONDecodeError, ValueError):
            errors = ['evidence_unavailable_or_invalid']
        if errors:
            print('Operational-reliability evidence FAILED: ' + ', '.join(errors))
            return 1
        print(f'Operational-reliability evidence PASS: {args.output}')
        return 0
    report = qualify(args.output.resolve())
    if report.get('repository_operations_status') != 'PASS':
        print('Operational-reliability qualification FAILED: ' + ', '.join(report.get('validation_errors', ['scenario_failed'])))
        return 1
    print(f'Operational-reliability qualification PASS: {args.output.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
