from __future__ import annotations
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Union
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.platform.configuration_contract import (
    ConfigurationContractError,
    collect_webhook_secrets,
    validate_environment_namespace,
)
from app.platform.version import VERSION

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
from scripts.release_version import ReleaseVersionError, current_release_paths, parse_candidate_version


COMPANY_QUALIFICATION_SCHEMA_VERSION = 2
COMPANY_QUALIFICATION_PROJECT = 'react-fastapi-base'
COMPANY_QUALIFICATION_PROFILE = 'company'
REPOSITORY_RELEASE_IDENTITY_PATH = current_release_paths(REPOSITORY_ROOT).identity
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
GateId = Literal[
    'technical_release',
    'identity',
    'storage',
    'deployment',
    'ui_accessibility',
    'performance',
    'operations',
    'release_evidence',
]
GateStatus = Literal['PASS', 'BLOCKED', 'FAIL']
StorageKind = Literal['local_disk', 'provider_supported_posix']

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


def _validate_safe_metadata(value: str, field_name: str) -> str:
    value = _validate_attestation(value)
    lowered = value.casefold()
    if any(token in lowered for token in ('accesskey', 'password', 'credential', 'authorization', 'cookie', 'secret', 'token')):
        raise ValueError(f'{field_name} must not contain credential-bearing material.')
    if re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', lowered):
        raise ValueError(f'{field_name} must not contain a fingerprint.')
    return value


def _validate_commit(value: str, field_name: str) -> str:
    if not re.fullmatch(r'[0-9a-fA-F]{40}', value):
        raise ValueError(f'{field_name} must be a full executable-source commit.')
    return value.lower()


def _validate_digest(value: str, field_name: str) -> str:
    if not re.fullmatch(r'[0-9a-fA-F]{64}', value):
        raise ValueError(f'{field_name} must be a SHA-256 source digest.')
    return value.lower()


def _validate_candidate_version(value: str) -> str:
    try:
        return parse_candidate_version(value).version
    except ReleaseVersionError as error:
        raise ValueError('Qualification candidate version is invalid.') from error


def _validate_repository_locator(value: str, field_name: str) -> str:
    value = _validate_safe_metadata(value, field_name)
    parsed = urlsplit(value)
    if parsed.scheme or parsed.username or parsed.password or parsed.query or parsed.fragment or value.startswith('/'):
        raise ValueError(f'{field_name} must be a relative repository locator.')
    return value


class EvidenceReference(BaseModel):
    """Durable locator and identity metadata, never an evidence payload."""

    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal[
        'release_manifest',
        'readiness_matrix',
        'verification_report',
        'identity_proof',
        'storage_proof',
        'deployment_proof',
        'accessibility_report',
        'performance_report',
        'operations_report',
        'approval_record',
    ]
    locator: str = Field(min_length=1, max_length=512)
    evidence_id: str = Field(min_length=1, max_length=160)
    issuer: str = Field(min_length=1, max_length=160)

    @field_validator('locator')
    @classmethod
    def safe_locator(cls, value: str) -> str:
        value = _validate_safe_metadata(value, 'Evidence locator')
        parsed = urlsplit(value)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Evidence locator must not contain credentials, query parameters or fragments.')
        if parsed.scheme and parsed.scheme not in ('http', 'https'):
            raise ValueError('Evidence locator must use HTTPS/HTTP or a relative repository locator.')
        if value.startswith('/'):
            raise ValueError('Evidence locator must not expose an absolute filesystem path.')
        return value

    @field_validator('evidence_id', 'issuer')
    @classmethod
    def safe_identity_metadata(cls, value: str) -> str:
        return _validate_safe_metadata(value, 'Evidence identity metadata')


class TechnicalReleaseFacts(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal['technical_release'] = 'technical_release'
    code_ready: Literal[True]
    candidate_version: str = Field(min_length=1, max_length=64)
    verified_source_commit: str
    source_digest: str

    @field_validator('verified_source_commit')
    @classmethod
    def full_source_commit(cls, value: str) -> str:
        return _validate_commit(value, 'Technical release source commit')

    @field_validator('source_digest')
    @classmethod
    def source_sha256(cls, value: str) -> str:
        return _validate_digest(value, 'Technical release source digest')


class IdentityFacts(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal['identity'] = 'identity'
    identity_topology: Literal['per_user_process']
    simultaneous_real_user_evidence: Literal[True]


class StorageFacts(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal['storage'] = 'storage'
    storage_kind: StorageKind
    provider_sqlite_support_reference: str = Field(min_length=8, max_length=512)
    all_database_clients_same_host: Literal[True]
    persistent_root: str

    @field_validator('provider_sqlite_support_reference')
    @classmethod
    def safe_provider_reference(cls, value: str) -> str:
        return _validate_safe_metadata(value, 'Provider SQLite support reference')

    @field_validator('persistent_root')
    @classmethod
    def absolute_storage_root(cls, value: str) -> str:
        return _validate_absolute_root(value)


class DeploymentFacts(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal['deployment'] = 'deployment'
    deployment_id: str = Field(min_length=1, max_length=160)
    ingress_authentication_evidence: Literal[True]
    redeploy_persistence_evidence: EvidenceReference
    restore_drill_evidence: EvidenceReference

    @field_validator('deployment_id')
    @classmethod
    def safe_deployment_id(cls, value: str) -> str:
        return _validate_safe_metadata(value, 'Deployment ID')


class UiAccessibilityFacts(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal['ui_accessibility'] = 'ui_accessibility'
    company_profile_evidence: Literal[True]


class PerformanceFacts(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal['performance'] = 'performance'
    company_profile_evidence: Literal[True]


class OperationsFacts(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal['operations'] = 'operations'
    company_profile_evidence: Literal[True]


class ReleaseEvidenceFacts(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    kind: Literal['release_evidence'] = 'release_evidence'
    project: str
    profile: str
    candidate_version: str = Field(min_length=1, max_length=64)
    verified_source_commit: str
    source_digest: str
    evidence_commit: str
    readiness_matrix_sha256: str
    target_base_sha: str | None = None
    accepted_head: str | None = None
    repository_merge_sha: str | None = None

    @field_validator('project', 'profile')
    @classmethod
    def safe_identity(cls, value: str) -> str:
        return _validate_safe_metadata(value, 'Release identity')

    @field_validator('candidate_version')
    @classmethod
    def valid_candidate_version(cls, value: str) -> str:
        return _validate_candidate_version(value)

    @field_validator('verified_source_commit', 'evidence_commit', 'target_base_sha', 'accepted_head', 'repository_merge_sha')
    @classmethod
    def full_commits(cls, value: str | None, info) -> str | None:
        return None if value is None else _validate_commit(value, str(info.field_name))

    @field_validator('source_digest', 'readiness_matrix_sha256')
    @classmethod
    def digests(cls, value: str, info) -> str:
        return _validate_digest(value, str(info.field_name))

    @model_validator(mode='after')
    def post_acceptance_fields_are_semantic(self):
        if self.evidence_commit == self.verified_source_commit:
            raise ValueError('Evidence commit must remain distinct from verified executable source.')
        post_acceptance = (self.accepted_head, self.repository_merge_sha)
        if any(value in {self.verified_source_commit, self.evidence_commit, self.target_base_sha} for value in post_acceptance if value is not None):
            raise ValueError('Post-acceptance release identities must remain distinct from source, evidence and target base commits.')
        if self.repository_merge_sha is not None and self.repository_merge_sha == self.target_base_sha:
            raise ValueError('Repository merge SHA must not alias the target base SHA.')
        return self


class RepositorySourceEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    locator: str = Field(min_length=1, max_length=512)
    sha256: str

    @field_validator('locator')
    @classmethod
    def safe_locator(cls, value: str) -> str:
        return _validate_repository_locator(value, 'Repository source evidence locator')

    @field_validator('sha256')
    @classmethod
    def valid_sha256(cls, value: str) -> str:
        return _validate_digest(value, 'Repository source evidence digest')


class RepositoryReleaseIdentity(BaseModel):
    """Repository-generated identity independent of operator evidence."""

    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    schema_version: Literal[1] = 1
    identity_type: Literal['repository_release', 'repository_rc11_release', 'repository_rc12_release']
    project: Literal['react-fastapi-base']
    profile: Literal['company']
    candidate_version: str = Field(min_length=1, max_length=64)
    verified_source_commit: str
    source_digest: str
    source_evidence: RepositorySourceEvidence
    generated_by: Literal['scripts/generate_release_identity.py']
    code_ready: Literal[True]
    production_ready: Literal[False]
    release_status: Literal['NOT_CERTIFIED']

    @field_validator('candidate_version')
    @classmethod
    def valid_candidate_version(cls, value: str) -> str:
        return _validate_candidate_version(value)

    @field_validator('verified_source_commit')
    @classmethod
    def full_source_commit(cls, value: str) -> str:
        return _validate_commit(value, 'Repository release source commit')

    @field_validator('source_digest')
    @classmethod
    def source_sha256(cls, value: str) -> str:
        return _validate_digest(value, 'Repository release source digest')


QualificationFacts = Annotated[
    Union[
        TechnicalReleaseFacts,
        IdentityFacts,
        StorageFacts,
        DeploymentFacts,
        UiAccessibilityFacts,
        PerformanceFacts,
        OperationsFacts,
        ReleaseEvidenceFacts,
    ],
    Field(discriminator='kind'),
]


class CompanyQualificationGate(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    id: GateId
    status: GateStatus
    evidence: list[EvidenceReference] = Field(default_factory=list)
    facts: QualificationFacts | None = None
    reason: str | None = Field(default=None, max_length=512)

    @field_validator('reason')
    @classmethod
    def safe_reason(cls, value: str | None) -> str | None:
        return None if value is None else _validate_safe_metadata(value, 'Gate reason')

    @model_validator(mode='after')
    def facts_match_gate(self):
        if self.facts is not None and self.facts.kind != self.id:
            raise ValueError('Gate facts must match the gate ID.')
        if self.status == 'PASS' and (not self.evidence or self.facts is None):
            raise ValueError('A PASS gate requires evidence and typed facts.')
        if self.status in ('BLOCKED', 'FAIL') and not self.reason:
            raise ValueError('A BLOCKED or FAIL gate requires a deterministic reason.')
        if self.status == 'PASS' and self.reason is not None:
            raise ValueError('A PASS gate must not carry a blocking reason.')
        return self


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
    """Final composite production qualification, not an operator assertion."""
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    schema_version: Literal[2] = COMPANY_QUALIFICATION_SCHEMA_VERSION
    project: str = COMPANY_QUALIFICATION_PROJECT
    profile: str = COMPANY_QUALIFICATION_PROFILE
    candidate_version: str | None = None
    verified_source_commit: str | None = None
    source_digest: str | None = None
    deployment_id: str | None = None
    identity_topology: Literal['per_user_process'] | None = None
    storage_kind: StorageKind | None = None
    provider_sqlite_support_reference: str | None = None
    all_database_clients_same_host: Literal[True] | None = None
    persistent_root: str | None = None
    gates: list[CompanyQualificationGate] = Field(default_factory=list)
    approved_by: str | None = None
    approved_at: str | None = None

    @field_validator('project', 'profile')
    @classmethod
    def safe_binding_identity(cls, value: str) -> str:
        return _validate_safe_metadata(value, 'Qualification binding')

    @field_validator('candidate_version')
    @classmethod
    def safe_candidate_version(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_candidate_version(value)

    @field_validator('verified_source_commit')
    @classmethod
    def safe_verified_commit(cls, value: str | None) -> str | None:
        return None if value is None else _validate_commit(value, 'Qualification source commit')

    @field_validator('source_digest')
    @classmethod
    def safe_source_digest(cls, value: str | None) -> str | None:
        return None if value is None else _validate_digest(value, 'Qualification source digest')

    @field_validator('deployment_id', 'provider_sqlite_support_reference')
    @classmethod
    def safe_infrastructure_reference(cls, value: str | None) -> str | None:
        return None if value is None else _validate_safe_metadata(value, 'Qualification infrastructure reference')

    @field_validator('persistent_root')
    @classmethod
    def absolute_qualification_root(cls, value: str | None) -> str | None:
        return None if value is None else _validate_absolute_root(value)

    @field_validator('approved_by')
    @classmethod
    def safe_approver(cls, value: str | None) -> str | None:
        return None if value is None else _validate_safe_metadata(value, 'Qualification approver')

    @field_validator('approved_at')
    @classmethod
    def timestamped_approval(cls, value: str | None) -> str | None:
        return None if value is None else _validate_timezone_timestamp(value)

    @model_validator(mode='after')
    def exact_gate_set(self):
        ids = [gate.id for gate in self.gates]
        if len(ids) != len(set(ids)):
            raise ValueError('Company qualification gates must not contain duplicates.')
        if set(ids) != set(MANDATORY_GATE_IDS):
            raise ValueError('Company qualification gates must contain exactly the mandatory gate set.')
        return self

    def gate(self, gate_id: str) -> CompanyQualificationGate | None:
        return next((gate for gate in self.gates if gate.id == gate_id), None)

    def contract_errors(self) -> list[str]:
        errors: list[str] = []
        if self.project != COMPANY_QUALIFICATION_PROJECT:
            errors.append('Qualification project binding is invalid.')
        if self.profile != COMPANY_QUALIFICATION_PROFILE:
            errors.append('Qualification profile binding is invalid.')
        for field_name in ('candidate_version', 'verified_source_commit', 'source_digest', 'deployment_id', 'identity_topology', 'storage_kind', 'provider_sqlite_support_reference', 'all_database_clients_same_host', 'persistent_root'):
            if getattr(self, field_name) is None:
                errors.append(f'Qualification binding field {field_name} is missing.')
        if self.approved_by is None or self.approved_at is None:
            errors.append('Qualification approval metadata is missing.')
        ids = [gate.id for gate in self.gates]
        if len(ids) != len(set(ids)):
            errors.append('Qualification gates contain duplicates.')
        missing = sorted(set(MANDATORY_GATE_IDS) - set(ids))
        if missing:
            errors.append('Qualification gates are missing: ' + ', '.join(missing) + '.')
        for gate in self.gates:
            if gate.status != 'PASS':
                errors.append(f'Qualification gate {gate.id} is {gate.status}.')
            elif not gate.evidence:
                errors.append(f'Qualification gate {gate.id} has no evidence.')
            elif gate.facts is None:
                errors.append(f'Qualification gate {gate.id} has no typed facts.')
        technical_gate = self.gate('technical_release')
        if isinstance(technical_gate.facts if technical_gate else None, TechnicalReleaseFacts):
            facts = technical_gate.facts
            if facts.candidate_version != self.candidate_version or facts.verified_source_commit != self.verified_source_commit or facts.source_digest != self.source_digest:
                errors.append('Technical release facts do not match the qualification source binding.')
        identity_gate = self.gate('identity')
        if isinstance(identity_gate.facts if identity_gate else None, IdentityFacts) and identity_gate.facts.identity_topology != self.identity_topology:
            errors.append('Identity facts do not match the qualification identity binding.')
        storage_gate = self.gate('storage')
        if isinstance(storage_gate.facts if storage_gate else None, StorageFacts):
            facts = storage_gate.facts
            if facts.storage_kind != self.storage_kind or facts.provider_sqlite_support_reference != self.provider_sqlite_support_reference or facts.all_database_clients_same_host != self.all_database_clients_same_host or facts.persistent_root != self.persistent_root:
                errors.append('Storage facts do not match the qualification storage binding.')
        deployment_gate = self.gate('deployment')
        if isinstance(deployment_gate.facts if deployment_gate else None, DeploymentFacts) and deployment_gate.facts.deployment_id != self.deployment_id:
            errors.append('Deployment facts do not match the qualification deployment binding.')
        errors.extend(self.release_evidence_binding_errors())
        return sorted(set(errors))

    def release_evidence_binding_errors(self) -> list[str]:
        gate = self.gate('release_evidence')
        if gate is None or gate.status != 'PASS' or not isinstance(gate.facts, ReleaseEvidenceFacts):
            return []
        facts = gate.facts
        errors: list[str] = []
        if facts.project != self.project or facts.project != COMPANY_QUALIFICATION_PROJECT:
            errors.append('Release evidence project binding does not match qualification.')
        if facts.profile != self.profile or facts.profile != COMPANY_QUALIFICATION_PROFILE:
            errors.append('Release evidence profile binding does not match qualification.')
        if facts.candidate_version != self.candidate_version:
            errors.append('Release evidence version binding does not match qualification.')
        if facts.verified_source_commit != self.verified_source_commit:
            errors.append('Release evidence verified-source binding does not match qualification.')
        if facts.source_digest != self.source_digest:
            errors.append('Release evidence source-digest binding does not match qualification.')
        return errors

    def repository_release_identity_errors(self, expected: RepositoryReleaseIdentity) -> list[str]:
        errors: list[str] = []
        for field_name, label in (
            ('project', 'project'),
            ('profile', 'profile'),
            ('candidate_version', 'version'),
            ('verified_source_commit', 'verified executable source commit'),
            ('source_digest', 'executable source digest'),
        ):
            if getattr(self, field_name) != getattr(expected, field_name):
                errors.append(f'Qualification {label} does not match the repository release identity.')

        technical_gate = self.gate('technical_release')
        technical_facts = technical_gate.facts if technical_gate else None
        if isinstance(technical_facts, TechnicalReleaseFacts):
            if technical_facts.candidate_version != expected.candidate_version:
                errors.append('Technical release version does not match the repository release identity.')
            if technical_facts.verified_source_commit != expected.verified_source_commit:
                errors.append('Technical release source commit does not match the repository release identity.')
            if technical_facts.source_digest != expected.source_digest:
                errors.append('Technical release source digest does not match the repository release identity.')

        release_gate = self.gate('release_evidence')
        release_facts = release_gate.facts if release_gate else None
        if isinstance(release_facts, ReleaseEvidenceFacts):
            if release_facts.project != expected.project:
                errors.append('Release evidence project does not match the repository release identity.')
            if release_facts.profile != expected.profile:
                errors.append('Release evidence profile does not match the repository release identity.')
            if release_facts.candidate_version != expected.candidate_version:
                errors.append('Release evidence version does not match the repository release identity.')
            if release_facts.verified_source_commit != expected.verified_source_commit:
                errors.append('Release evidence source commit does not match the repository release identity.')
            if release_facts.source_digest != expected.source_digest:
                errors.append('Release evidence source digest does not match the repository release identity.')
        return sorted(set(errors))

    def binding_errors(
        self,
        *,
        expected_version: str,
        expected_deployment_id: str,
        expected_root: Path,
        expected_release_identity: RepositoryReleaseIdentity | None = None,
    ) -> list[str]:
        errors: list[str] = []
        if self.candidate_version != expected_version:
            errors.append('Qualification belongs to a different candidate version.')
        if self.deployment_id != expected_deployment_id:
            errors.append('Qualification belongs to a different deployment.')
        if self.persistent_root is None or Path(self.persistent_root).resolve() != expected_root.resolve():
            errors.append('Qualification belongs to a different persistent root.')
        storage_gate = self.gate('storage')
        if isinstance(storage_gate.facts if storage_gate else None, StorageFacts):
            if storage_gate.facts.persistent_root != self.persistent_root:
                errors.append('Storage qualification belongs to a different persistent root.')
            if storage_gate.facts.storage_kind != self.storage_kind:
                errors.append('Storage qualification kind does not match the infrastructure binding.')
        deployment_gate = self.gate('deployment')
        if isinstance(deployment_gate.facts if deployment_gate else None, DeploymentFacts) and deployment_gate.facts.deployment_id != self.deployment_id:
            errors.append('Deployment qualification belongs to a different deployment.')
        if expected_release_identity is None:
            errors.append('Repository release identity is unavailable; production qualification is refused.')
        else:
            errors.extend(self.repository_release_identity_errors(expected_release_identity))
        return errors 

    def derived_production_ready(
        self,
        *,
        expected_version: str,
        expected_deployment_id: str,
        expected_root: Path,
        expected_release_identity: RepositoryReleaseIdentity | None = None,
    ) -> bool:
        return not self.contract_errors() and not self.binding_errors(
            expected_version=expected_version,
            expected_deployment_id=expected_deployment_id,
            expected_root=expected_root,
            expected_release_identity=expected_release_identity,
        )

    @property
    def production_ready(self) -> bool:
        """Derived internal contract state; this property is never serialized."""
        return not self.contract_errors()


class LegacyCompanyQualificationError(ValueError):
    """Schema-v1 infrastructure-only records require explicit requalification."""


def load_repository_release_identity(path: Path | None = None) -> RepositoryReleaseIdentity:
    identity_path = REPOSITORY_RELEASE_IDENTITY_PATH if path is None else path
    try:
        return RepositoryReleaseIdentity.model_validate_json(identity_path.read_text(encoding='utf-8'))
    except (OSError, ValueError, ValidationError) as error:
        raise ValueError('Repository release identity is missing or invalid.') from error


def load_company_qualification(payload: str) -> CompanyQualification:
    try:
        raw = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError('Company qualification is not valid JSON.') from error
    if isinstance(raw, dict) and raw.get('schema_version') == 1:
        raise LegacyCompanyQualificationError(
            'Company qualification uses legacy schema_version 1 infrastructure-only data; requalify with schema_version 2.'
        )
    return CompanyQualification.model_validate(raw)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='BASE_', extra='forbid')
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
    csrf_secret: SecretStr = Field(default=SecretStr(''), repr=False)
    max_request_bytes: int = Field(default=2_000_000, ge=1024, le=20_000_000)
    busy_timeout_ms: int = Field(default=5000, ge=100, le=30000)
    request_limit_per_minute: int = Field(default=180, ge=10, le=10000)
    enable_docs: bool = False
    webhook_allowed_hosts: list[str] = Field(default_factory=list)
    attachment_upload_mode: Literal['disabled', 'trusted_types', 'scanner_required'] = 'scanner_required'
    webhook_secrets: dict[str, SecretStr] = Field(default_factory=dict, repr=False, exclude=True)

    def __init__(self, **values):
        try:
            validate_environment_namespace(os.environ)
            explicit_webhook_secrets = values.get('webhook_secrets')
            if explicit_webhook_secrets is None:
                environment_secrets = collect_webhook_secrets(os.environ)
                if environment_secrets:
                    values['webhook_secrets'] = environment_secrets
            super().__init__(**values)
        except ConfigurationContractError:
            raise
        except ValidationError as error:
            # Pydantic's detailed errors can echo an invalid secret input.
            # Preserve the typed loader while returning only field names/types.
            locations = sorted({'.'.join(str(part) for part in item.get('loc', ())) for item in error.errors()})
            fields = ', '.join(location or 'configuration' for location in locations)
            raise ConfigurationContractError(f'Invalid configuration for {fields}.') from error

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

    def configuration_errors(self) -> list[str]:
        """Pure profile/environment/key/format/requiredness validation.

        This method never reads qualification files or probes storage/scanners.
        Those runtime-dependent checks remain owned by the selected deployment
        adapter and are intentionally reported separately.
        """
        errors: list[str] = []
        production_like = self.environment in ('qualification', 'production')
        if production_like and self.profile != 'company':
            errors.append('Qualification/production requires the company profile.')
        if production_like and not self.data_root.is_absolute():
            errors.append('Qualification/production data root must be absolute.')
        if production_like and (not self.deployment_id.strip() or self.deployment_id.strip().casefold() == 'local'):
            errors.append('Qualification/production requires an explicit deployment binding.')
        if production_like and (not self.allowed_origins or any(not origin.startswith('https://') for origin in self.allowed_origins)):
            errors.append('Qualification/production requires explicit HTTPS origins.')
        if production_like and (not self.allowed_hosts or any(host in ('*', 'localhost', '127.0.0.1', 'testserver') for host in self.allowed_hosts)):
            errors.append('Qualification/production requires explicit deployment hosts.')
        if production_like and len(self.csrf_secret.get_secret_value()) < 32:
            errors.append('Qualification/production requires BASE_CSRF_SECRET with at least 32 characters.')
        if production_like and not self.app_config.is_absolute():
            errors.append('Qualification/production app configuration path must be absolute.')
        if production_like and not self.policy_config.is_absolute():
            errors.append('Qualification/production policy configuration path must be absolute.')
        if self.environment == 'qualification' and self.qualification_prerequisites_file is None:
            errors.append('Qualification requires an explicit prerequisites file reference.')
        if self.environment == 'production' and self.qualification_file is None:
            errors.append('Production requires an explicit final qualification file reference.')
        return errors

    def assert_configuration(self) -> None:
        errors = self.configuration_errors()
        if errors:
            raise ConfigurationContractError('Configuration refused: ' + ' '.join(errors))

    def webhook_secret(self, reference: str) -> str:
        if not reference or not reference.isascii() or not reference[0].isalpha() or reference != reference.upper() or any(char not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for char in reference):
            raise ConfigurationContractError('Webhook secret reference is invalid.')
        secret = self.webhook_secrets.get(reference)
        # Operator/test processes may inject a handle after a long-lived
        # Settings instance was created.  Keep the lookup typed and redacted
        # at this boundary; webhook code never reads the environment directly.
        if secret is None:
            current = collect_webhook_secrets(os.environ).get(reference)
            if current is not None:
                secret = SecretStr(current)
        if secret is None or len(secret.get_secret_value()) < 32:
            raise ConfigurationContractError('Webhook signing secret is unavailable or too short.')
        return secret.get_secret_value()

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
        if len(self.csrf_secret.get_secret_value()) < 32:
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
        expected_release_identity: RepositoryReleaseIdentity | None = None
        try:
            expected_release_identity = load_repository_release_identity()
        except ValueError:
            errors.append('Repository release identity is missing or invalid; production qualification is refused.')
        try:
            if self.qualification_file is None:
                raise ValueError('missing qualification file')
            report = load_company_qualification(self.qualification_file.read_text())
            errors.extend(report.contract_errors())
            errors.extend(report.binding_errors(
                expected_version=VERSION,
                expected_deployment_id=self.deployment_id,
                expected_root=self.data_root,
                expected_release_identity=expected_release_identity,
            ))
        except LegacyCompanyQualificationError as error:
            # Preserve a useful migration diagnostic without echoing the old
            # payload or allowing infrastructure-only facts to certify v2.
            errors.append(str(error))
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
        qualification prerequisites or the final production qualification,
        but scanner availability belongs to the ASGI upload surface and is
        checked by the corresponding readiness method.
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

    def derived_production_ready(self, *, scanner_is_noop: bool | None = None) -> bool:
        """Derive readiness from the final contract; never read an input flag."""
        return self.environment == 'production' and not self.production_errors(scanner_is_noop=scanner_is_noop)
