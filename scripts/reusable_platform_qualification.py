#!/usr/bin/env python3
"""Reconcile the source-bound reusable-platform qualification evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_version import read_candidate_version  # noqa: E402
from scripts.source_manifest import source_provenance  # noqa: E402

SHA = re.compile(r'^[0-9a-f]{40}$')
DIGEST = re.compile(r'^[0-9a-f]{64}$')
EXPECTED_APPS = {
    'operational-registry',
    'datacenter-estate',
    'system-architecture-studio',
    'engineering-knowledge-center',
    'risk-analysis-workspace',
    'research-laboratory',
    'program-planning',
}
REQUIRED_RESULT_NAMES = {
    'performance-contract',
    'backend-tests',
    'tooling-tests',
    'architecture',
    'security-source',
    'configuration-contract',
    'checkpoint-manifest',
    'version-metadata',
    'candidate-progression',
    'performance-owned-algorithms',
    'performance-stress',
    'generated-contracts',
    'ui-state-matrix-contract',
    'api-compatibility',
    'typescript-syntax-and-pure-client',
    'static-server',
    'localhost-http',
    'engineering-widget-layer',
    'required-catalog-completeness',
    'object-inclusive-backup-restore',
    'storage-qualification',
    'frontend-typecheck',
    'frontend-unit',
    'frontend-build',
    'frontend-storybook',
    'browser-e2e-accessibility',
    'ui-state-matrix-results',
    'performance-results',
    'npm-advisories',
    'python-advisories',
    'reference-apps',
    'upgrade-fixture',
}
DOC_COMMANDS = {
    'README.md': ('setup', 'seed-demo', 'start', 'contracts', 'architecture', 'verify'),
    'docs/MAC_QUICKSTART.md': ('lab', 'setup', 'seed-demo', 'start', 'lab-build', 'test-lab'),
    'docs/UPGRADING.md': ('create', 'upgrade-plan', 'upgrade-apply', 'upgrade-rollback', 'upgrade-fixture'),
}
EVIDENCE_PATHS = {
    'clean_clone': Path('evidence/current/full-stack/fresh-clone-macos.json'),
    'reference_apps': Path('evidence/current/release/reference-apps.json'),
    'upgrade_fixture': Path('evidence/current/full-stack/upgrade-fixture.json'),
    'storage_qualification': Path('evidence/current/storage/qualification.json'),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, label: str, problems: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f'{label}: missing or invalid JSON ({error}).')
        return None
    if not isinstance(value, dict):
        problems.append(f'{label}: evidence must be a JSON object.')
        return None
    return value


def _require(condition: bool, problems: list[str], message: str) -> None:
    if not condition:
        problems.append(message)


def _validate_source_binding(
    document: dict[str, Any] | None,
    *,
    label: str,
    expected_commit: str,
    expected_digest: str,
    problems: list[str],
) -> None:
    if document is None:
        return
    checkout = document.get('checkout_commit') or document.get('candidate_head')
    _require(isinstance(checkout, str) and SHA.fullmatch(checkout), problems, f'{label}: exact checkout/candidate HEAD is missing or invalid.')
    if isinstance(document.get('checkout_commit'), str) and isinstance(document.get('candidate_head'), str):
        _require(document['checkout_commit'] == document['candidate_head'], problems, f'{label}: checkout_commit and candidate_head disagree.')
    _require(document.get('executable_source_commit') == expected_commit, problems, f'{label}: executable source commit is stale or mismatched.')
    _require(document.get('source_commit') == expected_commit, problems, f'{label}: legacy source_commit is not the canonical executable source commit.')
    _require(document.get('source_digest') == expected_digest, problems, f'{label}: executable source digest is stale or mismatched.')
    _require(isinstance(document.get('hashes'), dict) and document['hashes'].get('source_digest') == expected_digest, problems, f'{label}: source digest hash evidence is missing or mismatched.')
    _require(document.get('result') == 'PASS' and document.get('exit_code') == 0, problems, f'{label}: proof did not pass.')


def _validate_clean_clone(document: dict[str, Any] | None, problems: list[str]) -> None:
    if document is None:
        return
    _require(document.get('schema_version') == 3, problems, 'clean-clone: stale evidence schema; rerun the exact-candidate proof.')
    _require(document.get('profile') == 'development', problems, 'clean-clone: development profile is not recorded.')
    for field in ('credential_free', 'default_runtime_non_secret', 'isolated_temp_directory', 'cache_isolated', 'preinstall_clean'):
        _require(document.get(field) is True, problems, f'clean-clone: {field} is not proven.')
    _require(document.get('candidate_result') == 'PASS', problems, 'clean-clone: portable candidate result is not PASS.')
    qualification = document.get('macos_qualification')
    _require(qualification in {'PASS', 'BLOCKED'}, problems, 'clean-clone: macOS qualification must be PASS or truthfully BLOCKED.')
    commands = document.get('commands')
    _require(isinstance(commands, list) and commands and all(row.get('exit_code') == 0 for row in commands if isinstance(row, dict)), problems, 'clean-clone: setup or maintained gate command failed.')
    command_names = {' '.join(row.get('command', [])) for row in commands if isinstance(row, dict)}
    for expected in ('python3 dev setup', 'python3 dev seed-demo', 'python3 dev contracts', 'python3 dev architecture', 'python3 scripts/catalog.py --check --release', 'npm run typecheck', 'npm run build', 'npm run build:storybook', 'python3 scripts/e2e_runner.py'):
        _require(any(expected in name for name in command_names), problems, f'clean-clone: documented gate is missing: {expected}.')


def _validate_reference_apps(document: dict[str, Any] | None, *, version: str, expected_commit: str, expected_digest: str, problems: list[str]) -> None:
    if document is None:
        return
    _require(document.get('schema_version') == 2, problems, 'reference-apps: stale evidence schema; rerun generation proof.')
    _require(document.get('profile') == 'development' and document.get('runtime_non_secret') is True, problems, 'reference-apps: development/non-secret runtime proof is missing.')
    apps = document.get('apps')
    _require(isinstance(apps, list) and {row.get('id') for row in apps if isinstance(row, dict)} == EXPECTED_APPS, problems, 'reference-apps: the maintained seven-app set is incomplete or changed.')
    required_steps = {'development-bootstrap-and-migration', 'contracts', 'frontend-install', 'frontend-typecheck', 'frontend-tests', 'frontend-build'}
    for row in apps if isinstance(apps, list) else []:
        label = f"reference-apps/{row.get('id', '<unknown>')}"
        lock = row.get('template_lock')
        _require(isinstance(lock, dict), problems, f'{label}: full template-lock provenance is missing.')
        if isinstance(lock, dict):
            _require(lock.get('schema_version') == 2 and lock.get('platform_version') == version, problems, f'{label}: template-lock version is stale.')
            _require(lock.get('executable_source_commit') == expected_commit and lock.get('source_digest') == expected_digest, problems, f'{label}: template-lock source provenance is stale or mismatched.')
            _require('reference_source_commit' not in lock and isinstance(lock.get('managed'), dict) and lock['managed'], problems, f'{label}: managed-core lock is structurally invalid or carries the obsolete reference commit.')
        steps = row.get('steps')
        names = {step.get('name') for step in steps if isinstance(step, dict)} if isinstance(steps, list) else set()
        _require(required_steps <= names, problems, f'{label}: required generation/bootstrap/frontend steps are missing.')
        _require(isinstance(steps, list) and all(step.get('exit_code') == 0 for step in steps if isinstance(step, dict)), problems, f'{label}: a generation/bootstrap/frontend step failed.')


def _validate_upgrade(document: dict[str, Any] | None, problems: list[str]) -> None:
    if document is None:
        return
    _require(document.get('schema_version') == 2, problems, 'upgrade-fixture: stale evidence schema; rerun the fixture.')
    _require(document.get('profile') == 'development' and document.get('application_owned_preserved') is True, problems, 'upgrade-fixture: development profile or app-owned preservation proof is missing.')
    names = {step.get('name') for step in document.get('steps', []) if isinstance(step, dict)}
    required = {
        'upgrade-plan', 'upgrade-apply', 'migration', 'contracts', 'frontend-install',
        'frontend-typecheck', 'frontend-tests', 'frontend-build', 'upgrade-rollback',
        'application-config-preserved-after-apply', 'application-data-preserved-after-apply',
        'application-config-preserved-after-rollback', 'application-data-preserved-after-rollback',
    }
    _require(required <= names, problems, 'upgrade-fixture: required plan/apply/migration/frontend/rollback/data steps are missing.')
    _require(all(step.get('exit_code') == 0 for step in document.get('steps', []) if isinstance(step, dict)), problems, 'upgrade-fixture: a fixture step failed.')
    plan = next((step for step in document.get('steps', []) if isinstance(step, dict) and step.get('name') == 'upgrade-plan'), None)
    _require(isinstance(plan, dict) and plan.get('conflicts') == 0 and isinstance(plan.get('plan_hash'), str) and DIGEST.fullmatch(plan['plan_hash']), problems, 'upgrade-fixture: exact conflict-free plan hash is missing.')
    rollback = next((step for step in document.get('steps', []) if isinstance(step, dict) and step.get('name') == 'upgrade-rollback'), None)
    _require(isinstance(rollback, dict) and rollback.get('integrity_restored') is True, problems, 'upgrade-fixture: managed-core rollback integrity was not restored.')


def _validate_storage(document: dict[str, Any] | None, problems: list[str]) -> None:
    if document is None:
        return
    _require(document.get('schema_version') == 1, problems, 'storage-qualification: stale evidence schema; rerun the storage proof.')
    _require(document.get('profile') == 'company', problems, 'storage-qualification: company profile binding is missing.')
    _require(document.get('production_ready') is False and document.get('production_approved') is False, problems, 'storage-qualification: repository proof must not claim production approval.')
    _require(document.get('companyqualification_boundary', {}).get('final_company_storage') == 'BLOCKED_EXTERNAL', problems, 'storage-qualification: final company storage must remain external.')
    checks = document.get('checks')
    _require(isinstance(checks, dict) and all(value is True for value in checks.values()), problems, 'storage-qualification: a storage contract check did not pass.')


def _dev_commands() -> set[str]:
    result = subprocess.run([sys.executable, 'dev', '--help'], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return set()
    match = re.search(r'\{([^}]+)\}', result.stdout)
    return {value.strip() for value in match.group(1).split(',')} if match else set()


def _validate_documentation(version: str, problems: list[str]) -> None:
    current_version_docs = ('README.md', 'docs/MAC_QUICKSTART.md', 'docs/UPGRADING.md', 'docs/RELEASE_STATUS.md', 'docs/MASTER_DESIGN.md')
    for relative in current_version_docs:
        path = ROOT / relative
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            problems.append(f'documentation/{relative}: missing.')
            continue
        _require(version in text, problems, f'documentation/{relative}: current VERSION is not recorded.')
    quickstart = (ROOT / 'docs/MAC_QUICKSTART.md').read_text(encoding='utf-8')
    _require('RC.3' not in quickstart and 'RC.3' not in quickstart.upper(), problems, 'documentation/MAC_QUICKSTART.md: stale RC.3 wording remains.')
    _require('reference_source_commit' not in (ROOT / 'scripts/template_tools.py').read_text(encoding='utf-8'), problems, 'documentation/template lock: obsolete reference_source_commit remains in the generator.')
    commands = _dev_commands()
    _require(commands, problems, 'documentation: dev entrypoint help is unavailable.')
    for relative, required in DOC_COMMANDS.items():
        text = (ROOT / relative).read_text(encoding='utf-8')
        for command in required:
            _require(f'python3 dev {command}' in text, problems, f'documentation/{relative}: command is not documented as python3 dev {command}.')
            _require(command in commands, problems, f'documentation/{relative}: command is not present in dev entrypoint: {command}.')


def build_qualification(
    *,
    results: list[dict[str, Any]],
    candidate_head: str,
    executable_source_commit: str,
    source_digest: str,
    output: Path = ROOT / 'evidence/current/reuse/qualification.json',
) -> dict[str, Any]:
    problems: list[str] = []
    version = read_candidate_version(ROOT).version
    _require(SHA.fullmatch(candidate_head), problems, 'aggregate: candidate checkout identity is invalid.')
    _require(SHA.fullmatch(executable_source_commit), problems, 'aggregate: executable source commit is invalid.')
    _require(DIGEST.fullmatch(source_digest), problems, 'aggregate: executable source digest is invalid.')
    statuses = {row.get('name'): row.get('status') for row in results if isinstance(row, dict)}
    fresh_name = 'macos-fresh-install' if statuses.get('macos-fresh-install') is not None else 'candidate-fresh-install'
    required_results = {*REQUIRED_RESULT_NAMES, fresh_name}
    for name in sorted(required_results):
        _require(statuses.get(name) == 'PASS', problems, f'aggregate: required maintained gate is not PASS: {name}.')

    documents: dict[str, dict[str, Any] | None] = {}
    for label, relative in EVIDENCE_PATHS.items():
        documents[label] = _load(ROOT / relative, label, problems)
        _validate_source_binding(documents[label], label=label, expected_commit=executable_source_commit, expected_digest=source_digest, problems=problems)
    _validate_clean_clone(documents['clean_clone'], problems)
    _validate_reference_apps(documents['reference_apps'], version=version, expected_commit=executable_source_commit, expected_digest=source_digest, problems=problems)
    _validate_upgrade(documents['upgrade_fixture'], problems)
    _validate_storage(documents['storage_qualification'], problems)
    _validate_documentation(version, problems)

    inputs = {label: {'locator': str(relative), 'sha256': _sha256(ROOT / relative) if (ROOT / relative).is_file() else None} for label, relative in EVIDENCE_PATHS.items()}
    status = 'PASS' if not problems else 'FAIL'
    report = {
        'schema_version': 1,
        'report_type': 'reusable-platform-qualification',
        'project': 'react-fastapi-base',
        'candidate_version': version,
        'candidate_head': candidate_head,
        'checkout_commit': candidate_head,
        'executable_source_commit': executable_source_commit,
        'source_digest': source_digest,
        'source_binding': {
            'candidate_checkout': candidate_head,
            'verified_executable_source': executable_source_commit,
            'source_digest': source_digest,
        },
        'inputs': inputs,
        'checks': {
            'maintained_gates': {name: statuses.get(name, 'MISSING') for name in sorted(required_results)},
            'clean_clone_bootstrap': documents['clean_clone'] is not None and not any(problem.startswith('clean-clone:') for problem in problems),
            'reference_app_generation': documents['reference_apps'] is not None and not any(problem.startswith('reference-apps/') for problem in problems),
            'upgrade_and_rollback': documents['upgrade_fixture'] is not None and not any(problem.startswith('upgrade-fixture:') for problem in problems),
            'storage_contract': documents['storage_qualification'] is not None and not any(problem.startswith('storage-qualification:') for problem in problems),
            'provenance': not any('source' in problem or 'template-lock' in problem or 'aggregate:' in problem for problem in problems),
            'documentation_and_commands': not any(problem.startswith('documentation/') for problem in problems),
        },
        'status': status,
        'result': status,
        'qualification_status': status,
        'code_ready': status == 'PASS',
        'production_ready': False,
        'company_qualification': {
            'status': 'BLOCKED_EXTERNAL',
            'production_ready': False,
            'gates': {name: 'BLOCKED_EXTERNAL' for name in ('identity', 'storage', 'deployment', 'operations')},
            'note': 'Reusable-platform PASS is repository evidence only; company identity, storage, deployment, operations and overall CompanyQualification remain external.',
        },
        'problems': sorted(problems),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', type=Path, default=ROOT / 'evidence/current/full-stack/verification.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/reuse/qualification.json')
    args = parser.parse_args()
    verification = _load(args.verification.resolve(), 'verification', [])
    if verification is None:
        print('Reusable-platform qualification FAILED: verification report is missing or invalid.')
        return 1
    provenance = source_provenance(ROOT)
    expected_commit = verification.get('executable_source_commit') or verification.get('source_commit')
    expected_digest = verification.get('source_digest')
    if expected_commit != provenance['executable_source_commit'] or expected_digest != provenance['source_digest']:
        print('Reusable-platform qualification FAILED: verification is stale or source-mismatched.')
        return 1
    report = build_qualification(
        results=verification.get('results', []),
        candidate_head=verification.get('candidate_head') or provenance['checkout_commit'],
        executable_source_commit=provenance['executable_source_commit'],
        source_digest=provenance['source_digest'],
        output=args.output.resolve(),
    )
    print(json.dumps({'qualification': str(args.output), 'status': report['status']}, sort_keys=True))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
