#!/usr/bin/env python3
"""Reconcile the repository-supported company storage contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

from app.platform.database import Database  # noqa: E402
from app.platform.migrations import assert_revision  # noqa: E402
from app.platform.provision import provision  # noqa: E402
from app.platform.settings import CompanyQualificationPrerequisites, Settings  # noqa: E402
from app.platform.storage import LocalFilesystemStorage  # noqa: E402
from app.profiles.company.storage import CompanyStorageAdapter  # noqa: E402
from app.profiles.company.storage_probe import probe  # noqa: E402
from app.profiles.development.storage import DevelopmentStorageAdapter  # noqa: E402
from app.profiles.storage import LocalStorageAdapter  # noqa: E402
from scripts.release_version import read_candidate_version  # noqa: E402
from scripts.source_manifest import source_provenance  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, label: str, problems: list[str]) -> dict[str, Any] | None:
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f'{label}: missing or invalid JSON ({type(error).__name__}).')
        return None
    if not isinstance(document, dict):
        problems.append(f'{label}: evidence must be a JSON object.')
        return None
    return document


def _require(condition: bool, problems: list[str], message: str) -> None:
    if not condition:
        problems.append(message)


def _source_binding(
    *,
    verification_path: Path | None,
    expected_commit: str | None,
    expected_digest: str | None,
    expected_head: str | None,
    expected_version: str | None,
    provenance: dict[str, str],
    problems: list[str],
) -> dict[str, str]:
    if verification_path is not None:
        verification = _load(verification_path, 'verification', problems)
        if verification is not None:
            expected_commit = verification.get('executable_source_commit') or verification.get('source_commit')
            expected_digest = verification.get('source_digest')
            expected_head = verification.get('candidate_head') or verification.get('checkout_commit')
            expected_version = verification.get('candidate_version')
            _require(verification.get('code_ready') is True, problems, 'verification: code_ready is not true.')
    _require(expected_commit == provenance['executable_source_commit'], problems, 'source: executable source commit is stale or mismatched.')
    _require(expected_digest == provenance['source_digest'], problems, 'source: executable source digest is stale or mismatched.')
    _require(expected_head == provenance['checkout_commit'], problems, 'source: candidate checkout identity is stale or mismatched.')
    _require(expected_version == read_candidate_version(ROOT).version, problems, 'source: candidate version is stale or mismatched.')
    return {
        'candidate_version': read_candidate_version(ROOT).version,
        'candidate_head': provenance['checkout_commit'],
        'executable_source_commit': provenance['executable_source_commit'],
        'source_digest': provenance['source_digest'],
    }


def _run_qualification_contract(problems: list[str]) -> bool:
    result = subprocess.run(
        [sys.executable, 'scripts/check_qualification_contract.py'],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
        check=False,
    )
    passed = result.returncode == 0
    _require(passed, problems, 'qualification-contract: typed model/schema/template check did not pass.')
    return passed


def _run_contract_fixture(problems: list[str]) -> dict[str, bool]:
    checks = {
        'explicit_company_adapter': False,
        'development_is_qualification_independent': False,
        'database_invariants': False,
        'object_storage_backup_mode': False,
        'profile_owned_operator_path': False,
        'storage_probe_contract': False,
        'qualification_contract': False,
    }
    checks['explicit_company_adapter'] = not issubclass(CompanyStorageAdapter, LocalStorageAdapter)
    _require(checks['explicit_company_adapter'], problems, 'adapter: CompanyStorageAdapter inherits development/local semantics.')

    cli_source = (ROOT / 'backend/app/cli.py').read_text(encoding='utf-8')
    checks['profile_owned_operator_path'] = (
        'runtime.object_storage' in cli_source
        and 'storage_factory=' in cli_source
        and 'Database(settings)' not in cli_source
        and 'LocalFilesystemStorage' not in cli_source
    )
    _require(checks['profile_owned_operator_path'], problems, 'operator: maintenance path bypasses the selected profile storage adapter.')

    with tempfile.TemporaryDirectory(prefix='react-fastapi-storage-') as raw:
        root = Path(raw) / 'company-root'
        prerequisites_path = Path(raw) / 'prerequisites.json'
        prerequisites_path.write_text(CompanyQualificationPrerequisites(
            deployment_id='storage-fixture',
            identity_topology='per_user_process',
            storage_kind='local_disk',
            provider_sqlite_support_reference='fixture-provider-reference',
            all_database_clients_same_host=True,
            persistent_root=str(root.resolve()),
            authorized_by='storage-fixture-operator',
            authorized_at='2026-09-19T00:00:00Z',
        ).model_dump_json(), encoding='utf-8')
        settings = Settings(
            environment='qualification',
            profile='company',
            data_root=root,
            qualification_prerequisites_file=prerequisites_path,
            deployment_id='storage-fixture',
        )
        company = CompanyStorageAdapter()
        database = company.build_database(settings)
        object_storage = company.build_object_storage(settings)
        restore_storage = company.build_restore_object_storage(settings, Path(raw) / 'restore-target')
        _require(isinstance(object_storage, LocalFilesystemStorage), problems, 'object storage: supported company adapter is not the POSIX filesystem adapter.')
        _require(getattr(object_storage, 'backup_mode', None) == 'application_snapshot', problems, 'object storage: application snapshot mode is not explicit.')
        _require(isinstance(restore_storage, LocalFilesystemStorage), problems, 'restore: company adapter did not own the target object-storage construction.')
        _require(restore_storage.root == (Path(raw) / 'restore-target' / 'objects').resolve(), problems, 'restore: target object storage is not bound to the restore root.')
        checks['object_storage_backup_mode'] = (
            isinstance(object_storage, LocalFilesystemStorage)
            and getattr(object_storage, 'backup_mode', None) == 'application_snapshot'
            and isinstance(restore_storage, LocalFilesystemStorage)
        )

        engine = database.engine(provision=True)
        with engine.connect() as connection:
            pragma = {
                'journal_mode': connection.exec_driver_sql('PRAGMA journal_mode').scalar(),
                'synchronous': connection.exec_driver_sql('PRAGMA synchronous').scalar(),
                'foreign_keys': connection.exec_driver_sql('PRAGMA foreign_keys').scalar(),
                'busy_timeout': connection.exec_driver_sql('PRAGMA busy_timeout').scalar(),
            }
        checks['database_invariants'] = pragma == {
            'journal_mode': 'delete',
            'synchronous': 2,
            'foreign_keys': 1,
            'busy_timeout': settings.busy_timeout_ms,
        }
        _require(checks['database_invariants'], problems, 'database: conservative SQLite invariants are not all active.')
        tenant_id = provision(database, 'Storage qualification fixture', 'storage.admin')
        assert_revision(database)
        assert_revision(database, tenant_id)
        database.close()

        development = DevelopmentStorageAdapter()
        development_settings = Settings(environment='test', profile='development', data_root=Path(raw) / 'development-root')
        development_database = development.build_database(development_settings)
        development_object_storage = development.build_object_storage(development_settings)
        checks['development_is_qualification_independent'] = (
            isinstance(development_database, Database)
            and isinstance(development_object_storage, LocalFilesystemStorage)
        )
        development_database.close()
        _require(checks['development_is_qualification_independent'], problems, 'development: storage construction unexpectedly depends on company qualification facts.')

        probe_result = probe(root, intended_root=root)
        checks['storage_probe_contract'] = (
            probe_result.get('diagnostic_pass') is True
            and probe_result.get('production_approved') is False
            and 'No cross-host test' in probe_result.get('limitations', [])
            and 'No power-loss test' in probe_result.get('limitations', [])
            and 'No provider compatibility guarantee' in probe_result.get('limitations', [])
        )
        _require(checks['storage_probe_contract'], problems, 'storage-probe: diagnostic-only boundary or limitations changed.')

    checks['qualification_contract'] = _run_qualification_contract(problems)
    return checks


def build_qualification(
    *,
    recovery_path: Path,
    output: Path,
    verification_path: Path | None = None,
    verified_source_commit: str | None = None,
    source_digest: str | None = None,
    candidate_head: str | None = None,
    candidate_version: str | None = None,
) -> dict[str, Any]:
    problems: list[str] = []
    provenance = source_provenance(ROOT)
    source = _source_binding(
        verification_path=verification_path,
        expected_commit=verified_source_commit,
        expected_digest=source_digest,
        expected_head=candidate_head,
        expected_version=candidate_version,
        provenance=provenance,
        problems=problems,
    )
    recovery = _load(recovery_path, 'recovery', problems)
    if recovery is not None:
        for field in ('candidate_head', 'checkout_commit'):
            _require(recovery.get(field) == source['candidate_head'], problems, f'recovery: {field} is stale or mismatched.')
        _require(recovery.get('executable_source_commit') == source['executable_source_commit'], problems, 'recovery: executable source commit is stale or mismatched.')
        _require(recovery.get('source_commit') == source['executable_source_commit'], problems, 'recovery: source commit is stale or mismatched.')
        _require(recovery.get('source_digest') == source['source_digest'], problems, 'recovery: source digest is stale or mismatched.')
        _require(recovery.get('result') == 'PASS' and recovery.get('exit_code') == 0, problems, 'recovery: object-inclusive recovery fixture did not pass.')
        object_hashes = [recovery.get(name) for name in ('source_object_sha', 'snapshot_object_sha', 'restored_object_sha', 'downloaded_object_sha')]
        _require(all(isinstance(value, str) and len(value) == 64 for value in object_hashes) and len(set(object_hashes)) == 1, problems, 'recovery: representative object bytes were not preserved.')

    checks = _run_contract_fixture(problems)
    status = 'PASS' if not problems else 'FAIL'
    report: dict[str, Any] = {
        'schema_version': 1,
        'report_type': 'repository-storage-qualification',
        'project': 'react-fastapi-base',
        'profile': 'company',
        'candidate_version': source['candidate_version'],
        'candidate_head': source['candidate_head'],
        'checkout_commit': source['candidate_head'],
        'executable_source_commit': source['executable_source_commit'],
        'source_commit': source['executable_source_commit'],
        'source_digest': source['source_digest'],
        'hashes': {'source_digest': source['source_digest']},
        'environment': {'platform': platform.system(), 'python': platform.python_version()},
        'inputs': {
            'recovery': {'locator': str(recovery_path.relative_to(ROOT)) if recovery_path.is_relative_to(ROOT) else str(recovery_path), 'sha256': _sha256(recovery_path) if recovery_path.is_file() else None},
            'qualification_contract': {'locator': 'deploy/company-qualification.schema.json', 'sha256': _sha256(ROOT / 'deploy/company-qualification.schema.json')},
        },
        'checks': checks,
        'status': status,
        'result': status,
        'exit_code': 0 if status == 'PASS' else 1,
        'code_ready': status == 'PASS',
        'production_ready': False,
        'production_approved': False,
        'companyqualification_boundary': {
            'final_company_storage': 'BLOCKED_EXTERNAL',
            'production_ready': False,
            'release_status': 'NOT_CERTIFIED',
            'reason': 'Repository/local storage evidence does not prove actual company provider SQLite semantics, durability, redeploy persistence or production-like backup/restore.',
        },
        'problems': sorted(set(problems)),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recovery', type=Path, default=ROOT / 'evidence/current/recovery/object-restore.json')
    parser.add_argument('--verification', type=Path)
    parser.add_argument('--verified-source-commit')
    parser.add_argument('--source-digest')
    parser.add_argument('--candidate-head')
    parser.add_argument('--candidate-version')
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/storage/qualification.json')
    args = parser.parse_args()
    if args.verification is None and not all((args.verified_source_commit, args.source_digest, args.candidate_head, args.candidate_version)):
        args.verification = ROOT / 'evidence/current/full-stack/verification.json'
    report = build_qualification(
        recovery_path=args.recovery.resolve(),
        output=args.output.resolve(),
        verification_path=args.verification.resolve() if args.verification is not None else None,
        verified_source_commit=args.verified_source_commit,
        source_digest=args.source_digest,
        candidate_head=args.candidate_head,
        candidate_version=args.candidate_version,
    )
    print(json.dumps({'qualification': str(args.output), 'status': report['status']}, sort_keys=True))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Storage qualification FAILED: {error}')
        raise SystemExit(1) from None
