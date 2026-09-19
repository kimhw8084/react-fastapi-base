#!/usr/bin/env python3
"""Run a disposable generated-app upgrade, migration, build, test and rollback proof."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / 'backend/.venv/bin/python'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.source_manifest import source_provenance


def load_template_tools():
    spec = importlib.util.spec_from_file_location('template_tools', ROOT / 'scripts/template_tools.py')
    if spec is None or spec.loader is None:
        raise RuntimeError('Unable to load template tools.')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> dict:
    started = time.monotonic()
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    return {
        'command': command,
        'cwd': str(cwd),
        'exit_code': completed.returncode,
        'duration_seconds': round(time.monotonic() - started, 3),
        'stdout_tail': completed.stdout[-4000:],
        'stderr_tail': completed.stderr[-4000:],
    }


def app_data_check(app: Path, data_root: Path, *, seed: bool, tenant_id: str | None = None) -> dict:
    code = (
        "import json, os; from pathlib import Path; from fastapi.testclient import TestClient; "
        "from app.main import create_app; from app.platform.database import Database; "
        "from app.platform.provision import provision; from app.platform.settings import Settings; "
        "root=Path(os.environ['FIXTURE_DATA_ROOT']); settings=Settings(environment='test', profile='development', data_root=root, dev_user='alice'); "
    )
    if seed:
        code += (
            "database=Database(settings); tenant=provision(database, 'Upgrade fixture tenant', 'alice'); database.close(); "
            "app=create_app(settings); client=TestClient(app); "
            "bootstrap=client.get('/api/v1/bootstrap').json(); "
            "assert bootstrap['profile']=='development' and bootstrap['user_id']=='alice'; "
            "client.headers.update({'X-Tenant-Id':tenant,'X-CSRF-Token':bootstrap['csrf_token']}); "
            "created=client.post('/api/v1/projects', json={'title':'Application-owned project','summary':'survives managed core upgrade','status':'active','owner':'alice'}); "
            "assert created.status_code==201; print(json.dumps({'tenant_id':tenant,'project_id':created.json()['id'],'title':created.json()['title']})); client.close()"
        )
    else:
        code += (
            f"app=create_app(settings); tenant={tenant_id!r}; "
            "client=TestClient(app); "
            "bootstrap=client.get('/api/v1/bootstrap').json(); "
            "assert bootstrap['profile']=='development'; "
            "client.headers.update({'X-Tenant-Id':tenant,'X-CSRF-Token':bootstrap['csrf_token']}); "
            "listed=client.get('/api/v1/projects'); assert listed.status_code==200 and listed.json()['total']==1; "
            "project=listed.json()['items'][0]; assert project['title']=='Application-owned project'; "
            "assert 'AccessKey' not in str(bootstrap) and 'data_root' not in str(bootstrap); "
            "print(json.dumps({'tenant_id':tenant,'project_id':project['id'],'title':project['title']})); client.close()"
        )
    env = {key: value for key, value in os.environ.items() if not key.startswith('BASE_') and key != 'AccessKey'}
    env.update(FIXTURE_DATA_ROOT=str(data_root), PYTHONPATH=str(app / 'backend'))
    result = run([str(PYTHON), '-c', code], cwd=app / 'backend', env=env)
    if result['exit_code'] != 0:
        raise RuntimeError('Application-owned data fixture failed: ' + result['stderr_tail'] + result['stdout_tail'])
    try:
        payload = json.loads(str(result['stdout_tail']).strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as error:
        raise RuntimeError('Application-owned data fixture did not return a valid record.') from error
    return {'name': 'application-data-seed' if seed else 'application-data-check', **result, 'record': payload}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/release/upgrade-fixture.json')
    args = parser.parse_args()
    tools = load_template_tools()
    results: list[dict] = []
    started = time.monotonic()
    provenance = source_provenance(ROOT)

    with tempfile.TemporaryDirectory(prefix='react-fastapi-upgrade-') as raw:
        temp = Path(raw)
        old = temp / 'old-generated-app'
        incoming = temp / 'new-platform'
        tools.create_application(ROOT, old, 'upgrade-fixture', 'Upgrade Fixture')
        tools.create_application(ROOT, incoming, 'incoming-platform', 'Incoming Platform', 'clarity')

        managed = 'backend/app/platform/errors.py'
        path = incoming / managed
        path.write_text(path.read_text() + '\n# deterministic upgrade fixture change\n')
        incoming_lock = tools.validate_template_lock(incoming / 'template.lock.json')
        incoming_lock['managed'] = tools.core_manifest(incoming)
        (incoming / 'template.lock.json').write_text(json.dumps(incoming_lock, indent=2) + '\n')
        before = tools.core_manifest(old)
        application_config = old / 'backend/app/config/application.json'
        runtime_config = old / 'frontend/public/runtime-config.json'
        application_config.write_text(application_config.read_text().replace('Engineering Workspace', 'Upgrade Fixture Custom Application'))
        config_before = application_config.read_bytes()
        runtime_before = runtime_config.read_bytes()
        data_root = temp / 'database'
        seeded = app_data_check(old, data_root, seed=True)
        results.append(seeded)
        tenant_id = seeded['record']['tenant_id']
        plan = tools.upgrade_plan(old, incoming)
        results.append({'name': 'upgrade-plan', 'exit_code': 0 if plan['conflicts'] == 0 else 1, 'plan_hash': plan['plan_hash'], 'changes': len(plan['changes']), 'conflicts': plan['conflicts'], 'source_provenance': plan['incoming_provenance']})
        if plan['conflicts']:
            raise RuntimeError('Generated upgrade fixture unexpectedly contains conflicts.')

        journal = tools.upgrade_apply(old, incoming, plan['plan_hash'], 'APP-STOPPED')
        results.append({'name': 'upgrade-apply', 'exit_code': 0, 'journal': os.path.relpath(journal, old)})
        for row in plan['changes']:
            candidate = old / row['path']
            actual = tools.digest(candidate) if candidate.is_file() else None
            expected = row['incoming'] if row['action'] == 'update' else row['current'] if row['action'] == 'preserve_local' else None
            if actual != expected:
                raise RuntimeError(f'Upgrade apply did not match the reviewed plan for {row["path"]}.')
        if application_config.read_bytes() != config_before or runtime_config.read_bytes() != runtime_before:
            raise RuntimeError('Upgrade apply changed application-owned configuration.')
        results.append({'name': 'application-config-preserved-after-apply', 'exit_code': 0, 'preserved': True})
        results.append(app_data_check(old, data_root, seed=False, tenant_id=tenant_id))
        results[-1]['name'] = 'application-data-preserved-after-apply'

        env = {key: value for key, value in os.environ.items() if not key.startswith('BASE_') and key != 'AccessKey'}
        env.update(BASE_ENVIRONMENT='test', BASE_PROFILE='development', BASE_DATA_ROOT=str(data_root), PYTHONPATH=str(old / 'backend'))
        node_bins = sorted((Path.home() / '.nvm/versions/node').glob('v22*/bin'))
        if not node_bins:
            raise RuntimeError('Node 22 is required for the generated-app fixture.')
        env['PATH'] = str(node_bins[-1]) + os.pathsep + env.get('PATH', '')
        migration = run([
            str(PYTHON), '-c',
            f'from app.platform.settings import Settings; from app.platform.database import Database; from app.platform.migrations import migrate, assert_revision; s=Settings(environment="test", profile="development"); d=Database(s); migrate(d); migrate(d, "{tenant_id}"); assert_revision(d); assert_revision(d, "{tenant_id}")',
        ], cwd=old / 'backend', env=env)
        results.append({'name': 'migration', **migration})
        if migration['exit_code'] != 0:
            raise RuntimeError('Generated application migration failed: ' + migration['stderr_tail'] + migration['stdout_tail'])

        install = run(['npm', 'ci', '--ignore-scripts'], cwd=old / 'frontend', env=env)
        results.append({'name': 'frontend-install', **install})
        if install['exit_code'] != 0:
            raise RuntimeError('Generated application dependency install failed.')
        for name, command in (
            ('contracts', [str(PYTHON), 'scripts/generate_contracts.py']),
            ('frontend-typecheck', ['npm', 'run', 'typecheck']),
            ('frontend-tests', ['npm', 'test']),
            ('frontend-build', ['npm', 'run', 'build']),
        ):
            result = run(command, cwd=old if name == 'contracts' else old / 'frontend', env=env)
            result['name'] = name
            results.append(result)
            if result['exit_code'] != 0:
                raise RuntimeError(f'Generated application {name} failed: {result["stderr_tail"]}{result["stdout_tail"]}')

        tools.upgrade_rollback(old, journal, 'APP-STOPPED')
        after = tools.core_manifest(old)
        results.append({'name': 'upgrade-rollback', 'exit_code': 0, 'integrity_restored': before == after})
        if before != after:
            raise RuntimeError('Rollback did not restore the generated app managed-core digest.')
        if application_config.read_bytes() != config_before or runtime_config.read_bytes() != runtime_before:
            raise RuntimeError('Upgrade rollback changed application-owned configuration.')
        results.append({'name': 'application-config-preserved-after-rollback', 'exit_code': 0, 'preserved': True})
        results.append(app_data_check(old, data_root, seed=False, tenant_id=tenant_id))
        results[-1]['name'] = 'application-data-preserved-after-rollback'

    report = {
        'schema_version': 2,
        'candidate_head': provenance['checkout_commit'],
        'checkout_commit': provenance['checkout_commit'],
        'executable_source_commit': provenance['executable_source_commit'],
        'source_digest': provenance['source_digest'],
        'source_commit': provenance['executable_source_commit'],
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'command': ['python3', 'scripts/upgrade_fixture.py'],
        'exit_code': 0,
        'environment': {'platform': os.uname().sysname, 'machine': os.uname().machine, 'profile': 'development'},
        'hashes': {'source_digest': provenance['source_digest']},
        'profile': 'development',
        'application_owned_preserved': True,
        'result': 'PASS',
        'duration_seconds': round(time.monotonic() - started, 3),
        'steps': results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error))
        raise SystemExit(1)
