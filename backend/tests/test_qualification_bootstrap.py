import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import create_app
from app.platform.errors import AppError
from app.platform.settings import CompanyQualification, CompanyQualificationPrerequisites, Settings
from app.profiles.company.identity import CompanyIdentity


def _prerequisites(root: Path, *, deployment_id: str = 'qualification-fixture') -> CompanyQualificationPrerequisites:
    return CompanyQualificationPrerequisites(
        deployment_id=deployment_id,
        identity_topology='per_user_process',
        storage_kind='local_disk',
        provider_sqlite_support_reference='fixture-provider-reference',
        all_database_clients_same_host=True,
        persistent_root=str(root.resolve()),
        authorized_by='fixture-operator',
        authorized_at='2026-09-10T00:00:00Z',
    )


def _final_qualification(root: Path, *, deployment_id: str = 'qualification-fixture') -> CompanyQualification:
    return CompanyQualification(
        deployment_id=deployment_id,
        identity_topology='per_user_process',
        simultaneous_identity_evidence='fixture-identity-evidence',
        storage_kind='local_disk',
        provider_sqlite_support_reference='fixture-provider-reference',
        all_database_clients_same_host=True,
        persistent_root=str(root.resolve()),
        redeploy_persistence_evidence='fixture-redeploy-evidence',
        restore_drill_evidence='fixture-restore-evidence',
        ingress_authentication_evidence='fixture-ingress-evidence',
        approved_by='fixture-release-operator',
        approved_at='2026-09-10T00:00:00Z',
    )


def _qualification_settings(root: Path, prerequisites: Path) -> Settings:
    return Settings(
        environment='qualification',
        profile='company',
        data_root=root,
        allowed_origins=['https://frontend.example.com'],
        allowed_hosts=['backend.example.com'],
        csrf_secret='s' * 40,
        qualification_prerequisites_file=prerequisites,
        deployment_id='qualification-fixture',
        attachment_upload_mode='disabled',
    )


def _operator_env(root: Path, prerequisites: Path) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if not key.startswith('BASE_') and key != 'AccessKey'}
    environment.update({
        'AccessKey': 'company.alice',
        'BASE_ENVIRONMENT': 'qualification',
        'BASE_PROFILE': 'company',
        'BASE_DATA_ROOT': str(root),
        'BASE_QUALIFICATION_PREREQUISITES_FILE': str(prerequisites),
        'BASE_DEPLOYMENT_ID': 'qualification-fixture',
        'BASE_ALLOWED_ORIGINS': '["https://frontend.example.com"]',
        'BASE_ALLOWED_HOSTS': '["backend.example.com"]',
        'BASE_CSRF_SECRET': 's' * 40,
        'BASE_ATTACHMENT_UPLOAD_MODE': 'disabled',
    })
    return environment


def _run_operator(root: Path, prerequisites: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, '-m', 'app.cli', *args],
        cwd=Path(__file__).resolve().parents[1],
        env=_operator_env(root, prerequisites),
        text=True,
        capture_output=True,
        check=False,
    )


def test_prerequisite_schema_is_separate_and_strict(tmp_path):
    root = tmp_path / 'root'
    prerequisites = _prerequisites(root)
    assert prerequisites.identity_topology == 'per_user_process'
    assert prerequisites.all_database_clients_same_host is True
    with pytest.raises(ValidationError):
        CompanyQualificationPrerequisites.model_validate({**prerequisites.model_dump(), 'simultaneous_identity_evidence': 'not allowed'})


@pytest.mark.parametrize('field,value', [
    ('provider_sqlite_support_reference', 'tested'),
    ('persistent_root', 'relative-root'),
    ('identity_topology', 'shared_process'),
    ('storage_kind', 's3_fuse'),
    ('all_database_clients_same_host', False),
    ('authorized_at', '2026-09-10T00:00:00'),
])
def test_prerequisites_reject_unsafe_values(tmp_path, field, value):
    payload = _prerequisites(tmp_path / 'root').model_dump()
    payload[field] = value
    with pytest.raises(ValidationError):
        CompanyQualificationPrerequisites.model_validate(payload)


def test_qualification_requires_prerequisites_and_company_identity(tmp_path, monkeypatch):
    root = tmp_path / 'root'
    settings = Settings(environment='qualification', profile='company', data_root=root)
    assert any('prerequisites' in error for error in settings.qualification_errors())
    monkeypatch.delenv('AccessKey', raising=False)
    prerequisites_path = tmp_path / 'prerequisites.json'
    prerequisites_path.write_text(_prerequisites(root).model_dump_json())
    app = create_app(_qualification_settings(root, prerequisites_path))
    assert isinstance(app.state.identity, CompanyIdentity)
    with pytest.raises(AppError):
        with TestClient(app):
            pass


def test_qualification_startup_and_readiness_are_not_production_ready(tmp_path, monkeypatch):
    root = tmp_path / 'root'
    prerequisites_path = tmp_path / 'prerequisites.json'
    prerequisites_path.write_text(_prerequisites(root).model_dump_json())
    monkeypatch.setenv('AccessKey', 'company.alice')
    app = create_app(_qualification_settings(root, prerequisites_path))
    with TestClient(app, base_url='https://backend.example.com') as client:
        assert client.get('/api/v1/health').json()['alive'] is True
        readiness = client.get('/api/v1/readiness')
        assert readiness.status_code == 503
        assert readiness.json()['ready'] is False


def test_production_rejects_prerequisites_without_final_qualification(tmp_path):
    root = tmp_path / 'root'
    prerequisites_path = tmp_path / 'prerequisites.json'
    prerequisites_path.write_text(_prerequisites(root).model_dump_json())
    settings = Settings(
        environment='production', profile='company', data_root=root,
        allowed_origins=['https://frontend.example.com'], allowed_hosts=['backend.example.com'],
        csrf_secret='s' * 40, qualification_prerequisites_file=prerequisites_path,
        deployment_id='qualification-fixture', attachment_upload_mode='disabled',
    )
    assert any('Company qualification is missing or invalid' in error for error in settings.production_errors(scanner_is_noop=False))
    with pytest.raises(RuntimeError, match='Production refused'):
        settings.assert_safe(scanner_is_noop=False)


def test_production_operator_preflight_rejects_prerequisite_only(tmp_path):
    root = tmp_path / 'root'
    prerequisites_path = tmp_path / 'prerequisites.json'
    prerequisites_path.write_text(_prerequisites(root).model_dump_json())
    environment = _operator_env(root, prerequisites_path)
    environment['BASE_ENVIRONMENT'] = 'production'
    preflight = subprocess.run(
        [sys.executable, '-m', 'app.cli', 'preflight'],
        cwd=Path(__file__).resolve().parents[1], env=environment,
        text=True, capture_output=True, check=False,
    )
    assert preflight.returncode != 0
    payload = json.loads(preflight.stdout)
    assert payload['ready'] is False and payload['production_ready'] is False


def test_valid_final_qualification_passes_production_preflight(tmp_path):
    root = tmp_path / 'root'
    final_path = tmp_path / 'qualification.json'
    final_path.write_text(_final_qualification(root).model_dump_json())
    settings = Settings(
        environment='production', profile='company', data_root=root,
        allowed_origins=['https://frontend.example.com'], allowed_hosts=['backend.example.com'],
        csrf_secret='s' * 40, qualification_file=final_path,
        deployment_id='qualification-fixture', attachment_upload_mode='disabled',
    )
    assert settings.production_errors(scanner_is_noop=False) == []


def test_qualification_operator_flow_does_not_require_final_evidence(tmp_path, monkeypatch):
    root = tmp_path / 'root'
    prerequisites_path = tmp_path / 'prerequisites.json'
    prerequisites_path.write_text(_prerequisites(root).model_dump_json())
    preflight = _run_operator(root, prerequisites_path, 'preflight')
    assert preflight.returncode == 0, preflight.stdout + preflight.stderr
    assert json.loads(preflight.stdout)['production_ready'] is False

    provision = _run_operator(root, prerequisites_path, 'provision', '--tenant', 'Qualification Fixture', '--admin', 'company.alice')
    assert provision.returncode == 0, provision.stdout + provision.stderr
    tenant_id = provision.stdout.strip().splitlines()[-1]
    assert len(tenant_id) == 36

    add_member = _run_operator(root, prerequisites_path, 'add-member', '--tenant-id', tenant_id, '--user', 'company.bob', '--role', 'viewer')
    assert add_member.returncode == 0, add_member.stdout + add_member.stderr
    migrate = _run_operator(root, prerequisites_path, 'migrate', '--maintenance', 'APP-STOPPED')
    assert migrate.returncode == 0, migrate.stdout + migrate.stderr

    monkeypatch.setenv('AccessKey', 'company.alice')
    qualification_app = create_app(_qualification_settings(root, prerequisites_path).model_copy(update={'attachment_upload_mode': 'trusted_types'}))
    with TestClient(qualification_app, base_url='https://backend.example.com') as client:
        bootstrap = client.get('/api/v1/bootstrap')
        assert bootstrap.status_code == 200
        client.headers.update({'X-Tenant-Id': tenant_id, 'X-CSRF-Token': bootstrap.json()['csrf_token']})
        record = client.post('/api/v1/work-items', json={'title': 'Qualification recovery record'})
        assert record.status_code == 201
        body = b'qualification recovery bytes'
        attachment = client.post(
            f"/api/v1/work-items/{record.json()['id']}/attachments",
            json={'filename': 'qualification.txt', 'content_type': 'text/plain', 'content_base64': base64.b64encode(body).decode()},
        )
        assert attachment.status_code == 201
        readiness = client.get('/api/v1/readiness')
        assert readiness.status_code == 200
        assert readiness.json()['production_ready'] is False

    scratch = tmp_path / 'scratch'
    scratch.mkdir()
    doctor = _run_operator(root, prerequisites_path, 'doctor-storage', '--scratch-parent', str(scratch))
    assert doctor.returncode == 0, doctor.stdout + doctor.stderr
    assert json.loads(doctor.stdout)['production_approved'] is False

    snapshot = tmp_path / 'snapshot'
    backup = _run_operator(root, prerequisites_path, 'backup', '--output', str(snapshot), '--maintenance', 'APP-STOPPED')
    assert backup.returncode == 0, backup.stdout + backup.stderr
    restored = tmp_path / 'restored'
    restore = _run_operator(root, prerequisites_path, 'restore', '--snapshot', str(snapshot), '--target', str(restored))
    assert restore.returncode == 0, restore.stdout + restore.stderr

    restored_prerequisites_path = tmp_path / 'restored-prerequisites.json'
    restored_prerequisites_path.write_text(_prerequisites(restored).model_dump_json())
    restored_app = create_app(_qualification_settings(restored, restored_prerequisites_path).model_copy(update={'attachment_upload_mode': 'trusted_types'}))
    with TestClient(restored_app, base_url='https://backend.example.com') as client:
        bootstrap = client.get('/api/v1/bootstrap')
        assert bootstrap.status_code == 200
        client.headers.update({'X-Tenant-Id': tenant_id, 'X-CSRF-Token': bootstrap.json()['csrf_token']})
        recovered = client.get(f"/api/v1/work-items/{record.json()['id']}/attachments/{attachment.json()['id']}")
        assert recovered.status_code == 200
        assert recovered.content == body
        assert hashlib.sha256(recovered.content).hexdigest() == hashlib.sha256(body).hexdigest()

    seed = _run_operator(root, prerequisites_path, 'seed-demo')
    assert seed.returncode != 0
    assert 'forbidden' in (seed.stdout + seed.stderr).casefold()


def test_qualification_state_machine_fixture_can_transition_to_final_preflight(tmp_path, monkeypatch):
    root = tmp_path / 'root'
    prerequisites_path = tmp_path / 'prerequisites.json'
    prerequisites_path.write_text(_prerequisites(root).model_dump_json())
    provision = _run_operator(root, prerequisites_path, 'provision', '--tenant', 'Qualification Fixture', '--admin', 'company.alice')
    assert provision.returncode == 0, provision.stdout + provision.stderr
    monkeypatch.setenv('AccessKey', 'company.alice')
    qualification_app = create_app(_qualification_settings(root, prerequisites_path))
    with TestClient(qualification_app, base_url='https://backend.example.com') as client:
        readiness = client.get('/api/v1/readiness')
        assert readiness.status_code == 200
        readiness_payload = readiness.json()
        assert readiness_payload == {
            'ready': True,
            'version': readiness_payload['version'],
            'environment': 'qualification',
            'production_ready': False,
        }

    final_path = tmp_path / 'qualification.json'
    final_path.write_text(_final_qualification(root).model_dump_json())
    production_settings = Settings(
        environment='production', profile='company', data_root=root,
        allowed_origins=['https://frontend.example.com'], allowed_hosts=['backend.example.com'],
        csrf_secret='s' * 40, qualification_file=final_path,
        deployment_id='qualification-fixture', attachment_upload_mode='disabled',
    )
    production_app = create_app(production_settings)
    with TestClient(production_app, base_url='https://backend.example.com') as client:
        readiness = client.get('/api/v1/readiness')
        assert readiness.status_code == 200
        assert readiness.json()['production_ready'] is True
