from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_QUALIFICATION_PLACEHOLDERS = {
    'unqualified', 'placeholder', 'changeme', 'todo', 'tbd', 'n/a', 'none',
    'approved', 'tested', 'looks good',
}


def _validate_attestation(value: str) -> str:
    value = value.strip()
    if not value or any(ord(char) < 32 for char in value):
        raise ValueError('Qualification values must be non-empty and printable.')
    if value.casefold() in _QUALIFICATION_PLACEHOLDERS:
        raise ValueError('Qualification placeholders are not valid evidence.')
    return value


def _validate_absolute_root(value: str) -> str:
    if not Path(value).is_absolute():
        raise ValueError('Qualification persistent_root must be absolute.')
    return value


def _validate_timezone_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Qualification timestamp must be an ISO-8601 timestamp.') from error
    if parsed.tzinfo is None:
        raise ValueError('Qualification timestamp must include a timezone.')
    return value


class CompanyQualificationPrerequisites(BaseModel):
    """Pre-drill authorization facts, never final production evidence."""
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1] = 1
    deployment_id: str = Field(min_length=1)
    identity_topology: Literal['per_user_process']
    storage_kind: Literal['local_disk', 'provider_supported_posix']
    provider_sqlite_support_reference: str = Field(min_length=8)
    all_database_clients_same_host: Literal[True]
    persistent_root: str
    authorized_by: str = Field(min_length=1)
    authorized_at: str = Field(min_length=10)

    @field_validator('deployment_id', 'provider_sqlite_support_reference', 'persistent_root', 'authorized_by', 'authorized_at')
    @classmethod
    def nonblank_attestation(cls, value: str) -> str:
        return _validate_attestation(value)

    @field_validator('persistent_root')
    @classmethod
    def absolute_persistent_root(cls, value: str) -> str:
        return _validate_absolute_root(value)

    @field_validator('authorized_at')
    @classmethod
    def timestamped_authorization(cls, value: str) -> str:
        return _validate_timezone_timestamp(value)


class CompanyQualification(BaseModel):
    """Operator evidence, NOT a filesystem safety certificate issued by this code."""
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1] = 1
    deployment_id: str = Field(min_length=1)
    identity_topology: Literal['per_user_process']
    simultaneous_identity_evidence: str = Field(min_length=8)
    storage_kind: Literal['local_disk', 'provider_supported_posix']
    provider_sqlite_support_reference: str = Field(min_length=8)
    all_database_clients_same_host: Literal[True]
    persistent_root: str
    redeploy_persistence_evidence: str = Field(min_length=8)
    restore_drill_evidence: str = Field(min_length=8)
    ingress_authentication_evidence: str = Field(min_length=8)
    approved_by: str = Field(min_length=1)
    approved_at: str = Field(min_length=10)

    @field_validator('deployment_id', 'simultaneous_identity_evidence', 'provider_sqlite_support_reference', 'persistent_root', 'redeploy_persistence_evidence', 'restore_drill_evidence', 'ingress_authentication_evidence', 'approved_by', 'approved_at')
    @classmethod
    def nonblank_attestation(cls, value: str) -> str:
        return _validate_attestation(value)

    @field_validator('persistent_root')
    @classmethod
    def absolute_persistent_root(cls, value: str) -> str:
        return _validate_absolute_root(value)

    @field_validator('approved_at')
    @classmethod
    def timestamped_approval(cls, value: str) -> str:
        return _validate_timezone_timestamp(value)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='BASE_', extra='ignore')
    environment: Literal['development', 'test', 'qualification', 'production'] = 'production'
    profile: Literal['development', 'company'] = 'company'
    data_root: Path = Path('.local/data')
    app_config: Path = Path(__file__).resolve().parents[1] / 'config' / 'application.json'
    policy_config: Path = Path(__file__).resolve().parents[1] / 'config' / 'permissions.json'
    dev_user: str = 'demo.admin'
    allowed_origins: list[str] = Field(default_factory=lambda: ['http://127.0.0.1:5173', 'http://localhost:5173'])
    allowed_hosts: list[str] = Field(default_factory=lambda: ['127.0.0.1', 'localhost', 'testserver'])
    qualification_file: Path | None = None
    qualification_prerequisites_file: Path | None = None
    deployment_id: str = 'local'
    csrf_secret: str = ''
    max_request_bytes: int = Field(default=2_000_000, ge=1024, le=20_000_000)
    busy_timeout_ms: int = Field(default=5000, ge=100, le=30000)
    request_limit_per_minute: int = Field(default=180, ge=10, le=10000)
    enable_docs: bool = False
    webhook_allowed_hosts: list[str] = Field(default_factory=list)
    attachment_upload_mode: Literal['disabled', 'trusted_types', 'scanner_required'] = 'scanner_required'

    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, value: list[str]) -> list[str]:
        for origin in value:
            parsed = urlsplit(origin)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
                raise ValueError('CORS entries must be exact HTTP(S) origins.')
            if origin.endswith('/'):
                raise ValueError('Origin must not end in a slash.')
        return value

    @field_validator('webhook_allowed_hosts')
    @classmethod
    def validate_webhook_hosts(cls, value: list[str]) -> list[str]:
        clean=[]
        for host in value:
            host=host.strip().lower().rstrip('.')
            if not host or len(host)>253 or '/' in host or ':' in host or host in ('localhost','127.0.0.1','::1'):
                raise ValueError('Webhook allowlist entries must be exact public DNS hostnames.')
            if any(part=='' or len(part)>63 or not all(c.isalnum() or c=='-' for c in part) or part.startswith('-') or part.endswith('-') for part in host.split('.')):
                raise ValueError('Webhook allowlist entries must be exact public DNS hostnames.')
            clean.append(host)
        if len(set(clean))!=len(clean): raise ValueError('Webhook allowlist entries must be unique.')
        return clean

    def _common_company_errors(self, label: str) -> list[str]:
        errors: list[str] = []
        if self.profile != 'company':
            errors.append(f'{label} requires the company identity profile.')
        if not self.data_root.is_absolute():
            errors.append(f'{label} data root must be absolute and provisioned by the operator.')
        if not self.allowed_origins or any(not x.startswith('https://') for x in self.allowed_origins):
            errors.append(f'{label} requires explicit HTTPS frontend origins.')
        if not self.allowed_hosts or any(x in ('*', 'localhost', '127.0.0.1', 'testserver') for x in self.allowed_hosts):
            errors.append(f'{label} requires explicit deployment hostnames.')
        if len(self.csrf_secret) < 32:
            errors.append(f'{label} requires a randomly generated CSRF secret of at least 32 characters.')
        return errors

    def _upload_policy_errors(self, *, scanner_is_noop: bool | None, check_attachment_policy: bool, label: str) -> list[str]:
        errors: list[str] = []
        if check_attachment_policy and self.attachment_upload_mode == 'scanner_required':
            if scanner_is_noop is True:
                errors.append(f'{label} attachment uploads require a configured malware scanner; NoopMalwareScanner is not accepted.')
            elif scanner_is_noop is not False:
                errors.append(f'{label} attachment scanner status must be supplied before readiness can be approved.')
        return errors

    def _production_errors(self, *, scanner_is_noop: bool | None, check_attachment_policy: bool) -> list[str]:
        if self.environment != 'production':
            return []
        errors = self._common_company_errors('Production')
        errors.extend(self._upload_policy_errors(scanner_is_noop=scanner_is_noop, check_attachment_policy=check_attachment_policy, label='Production'))
        try:
            if self.qualification_file is None:
                raise ValueError('missing qualification file')
            report = CompanyQualification.model_validate_json(self.qualification_file.read_text())
            if report.deployment_id != self.deployment_id:
                errors.append('Qualification belongs to a different deployment.')
            if Path(report.persistent_root).resolve() != self.data_root.resolve():
                errors.append('Qualification belongs to a different persistent root.')
        except (ValueError, OSError):
            errors.append('Company qualification is missing or invalid; do not infer safe storage or per-user identity.')
        return errors

    def _qualification_errors(self, *, scanner_is_noop: bool | None, check_attachment_policy: bool) -> list[str]:
        if self.environment != 'qualification':
            return []
        errors = self._common_company_errors('Qualification')
        errors.extend(self._upload_policy_errors(scanner_is_noop=scanner_is_noop, check_attachment_policy=check_attachment_policy, label='Qualification'))
        try:
            if self.qualification_prerequisites_file is None:
                raise ValueError('missing qualification prerequisites file')
            report = CompanyQualificationPrerequisites.model_validate_json(self.qualification_prerequisites_file.read_text())
            if report.deployment_id != self.deployment_id:
                errors.append('Qualification prerequisites belong to a different deployment.')
            if Path(report.persistent_root).resolve() != self.data_root.resolve():
                errors.append('Qualification prerequisites belong to a different persistent root.')
        except (ValueError, OSError):
            errors.append('Qualification prerequisites are missing or invalid; final production evidence is not implied.')
        return errors

    def production_errors(self, *, scanner_is_noop: bool | None = None) -> list[str]:
        return self._production_errors(scanner_is_noop=scanner_is_noop, check_attachment_policy=True)

    def qualification_errors(self, *, scanner_is_noop: bool | None = None) -> list[str]:
        return self._qualification_errors(scanner_is_noop=scanner_is_noop, check_attachment_policy=True)

    def maintenance_errors(self) -> list[str]:
        """Validate an offline operator command without opening uploads.

        This is deliberately a separate API instead of a bypass flag on the
        application readiness check.  Maintenance commands still require the
        production qualification contract, but scanner availability belongs to
        the ASGI upload surface and is checked by ``production_errors``.
        """
        if self.environment == 'qualification':
            return self._qualification_errors(scanner_is_noop=False, check_attachment_policy=False)
        return self._production_errors(scanner_is_noop=False, check_attachment_policy=False)

    def assert_safe(self, *, scanner_is_noop: bool | None = None) -> None:
        errors = self.qualification_errors(scanner_is_noop=scanner_is_noop) if self.environment == 'qualification' else self.production_errors(scanner_is_noop=scanner_is_noop)
        if errors:
            prefix = 'Qualification' if self.environment == 'qualification' else 'Production'
            raise RuntimeError(prefix + ' refused: ' + ' '.join(errors))

    def assert_maintenance_safe(self) -> None:
        errors = self.maintenance_errors()
        if errors:
            prefix = 'Qualification' if self.environment == 'qualification' else 'Production'
            raise RuntimeError(prefix + ' refused: ' + ' '.join(errors))
