#!/usr/bin/env python3
"""Generate and verify the seven neutral reference applications from public APIs."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / 'backend/.venv/bin/python'
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.source_manifest import source_provenance
APPS = (
    ('operational-registry', 'Operational Registry', 'operations'),
    ('datacenter-estate', 'Datacenter Estate', 'operations'),
    ('system-architecture-studio', 'System Architecture Studio', 'clarity'),
    ('engineering-knowledge-center', 'Engineering Knowledge Center', 'clarity'),
    ('risk-analysis-workspace', 'Risk Analysis Workspace', 'operations'),
    ('research-laboratory', 'Research Laboratory', 'minimal'),
    ('program-planning', 'Program Planning', 'clarity'),
)


def template_tools():
    spec = importlib.util.spec_from_file_location('template_tools', ROOT / 'scripts/template_tools.py')
    if spec is None or spec.loader is None:
        raise RuntimeError('Unable to load template tools.')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(command: list[str], cwd: Path, env: dict[str, str]) -> dict:
    started = time.monotonic()
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    return {'command': command, 'exit_code': result.returncode, 'duration_seconds': round(time.monotonic() - started, 3), 'stdout_tail': result.stdout[-1200:], 'stderr_tail': result.stderr[-1200:]}


def main() -> int:
    output = ROOT / 'evidence/current/release/reference-apps.json'
    tools = template_tools()
    node_bins = sorted((Path.home() / '.nvm/versions/node').glob('v22*/bin'))
    if not node_bins:
        raise RuntimeError('Node 22 is required for reference app proof.')
    env = {key: value for key, value in os.environ.items() if not key.startswith('BASE_') and key != 'AccessKey'}
    env['PATH'] = str(node_bins[-1]) + os.pathsep + env.get('PATH', '')
    provenance = source_provenance(ROOT)
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    proof = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='react-fastapi-reference-apps-') as raw:
        root = Path(raw)
        for app_id, name, theme in APPS:
            app = root / app_id
            tools.create_application(ROOT, app, app_id, name, theme)
            config = json.loads((app / 'backend/app/config/application.json').read_text())
            runtime = json.loads((app / 'frontend/public/runtime-config.json').read_text())
            lock = tools.validate_template_lock(app / 'template.lock.json')
            if config['id'] != app_id or config['name'] != name or runtime['titleOverride'] != name:
                raise RuntimeError(f'Generated configuration mismatch for {app_id}.')
            if lock['platform_version'] != version or lock['executable_source_commit'] != provenance['executable_source_commit'] or lock['source_digest'] != provenance['source_digest']:
                raise RuntimeError(f'Template lock provenance mismatch for {app_id}.')
            if 'reference_source_commit' in lock or lock['managed'] != tools.core_manifest(app):
                raise RuntimeError(f'Template lock managed-core manifest mismatch for {app_id}.')
            runtime_text = json.dumps(runtime, sort_keys=True)
            config_text = json.dumps(config, sort_keys=True)
            if set(runtime) != {'schemaVersion', 'apiBase', 'defaultTheme', 'titleOverride'}:
                raise RuntimeError(f'Generated runtime configuration has an unsafe shape for {app_id}.')
            if any(token in (runtime_text + config_text).casefold() for token in ('accesskey', 'credential', 'password', 'authorization', 'secret', 'token')):
                raise RuntimeError(f'Generated public/configuration metadata is secret-like for {app_id}.')
            steps = []
            app_env = {**env, 'BASE_ENVIRONMENT': 'test', 'BASE_PROFILE': 'development', 'BASE_DATA_ROOT': str(root / f'{app_id}-runtime'), 'BASE_DEV_USER': 'demo.admin', 'PYTHONPATH': str(app / 'backend')}
            bootstrap = (
                "import tempfile; from pathlib import Path; "
                "from fastapi.testclient import TestClient; "
                "from app.main import create_app; "
                "from app.platform.database import Database; "
                "from app.platform.provision import provision; "
                "from app.platform.settings import Settings; "
                "root=Path(tempfile.mkdtemp(prefix='reference-app-runtime-')); "
                "settings=Settings(environment='test', profile='development', data_root=root, dev_user='demo.admin'); "
                "database=Database(settings); tenant=provision(database, 'Reference fixture', 'demo.admin'); database.close(); "
                "app=create_app(settings); client=TestClient(app); "
                "payload=client.get('/api/v1/bootstrap').json(); "
                "assert payload['profile']=='development' and payload['user_id']=='demo.admin'; "
                "client.headers.update({'X-Tenant-Id':tenant,'X-CSRF-Token':payload['csrf_token']}); "
                "created=client.post('/api/v1/projects', json={'title':'Reference project','summary':'fixture','status':'planned','owner':'demo.admin'}); "
                "assert created.status_code==201 and client.get('/api/v1/projects').json()['total']==1; "
                "assert 'AccessKey' not in str(payload) and 'data_root' not in str(payload) and 'profile_runtime' not in str(payload); client.close()"
            )
            steps.append({'name': 'development-bootstrap-and-migration', **run([str(PYTHON), '-c', bootstrap], app / 'backend', app_env)})
            steps.append({'name': 'contracts', **run([str(PYTHON), 'scripts/generate_contracts.py'], app, app_env)})
            for label, command in (('frontend-install', ['npm', 'ci', '--ignore-scripts']), ('frontend-typecheck', ['npm', 'run', 'typecheck']), ('frontend-tests', ['npm', 'test']), ('frontend-build', ['npm', 'run', 'build'])):
                steps.append({'name': label, **run(command, app / 'frontend', env)})
            if any(step['exit_code'] != 0 for step in steps):
                failed = next(step for step in steps if step['exit_code'] != 0)
                raise RuntimeError(f'Reference app proof failed for {app_id}: {failed}')
            proof.append({'id': app_id, 'name': name, 'theme': theme, 'steps': steps, 'template_lock': lock})
    report = {
        'schema_version': 2,
        'candidate_head': provenance['checkout_commit'],
        'checkout_commit': provenance['checkout_commit'],
        'executable_source_commit': provenance['executable_source_commit'],
        'source_digest': provenance['source_digest'],
        'source_commit': provenance['executable_source_commit'],
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'command': ['python3', 'scripts/reference_app_proof.py'],
        'exit_code': 0,
        'environment': {'platform': os.uname().sysname, 'machine': os.uname().machine, 'profile': 'development'},
        'hashes': {'source_digest': provenance['source_digest']},
        'profile': 'development',
        'runtime_non_secret': True,
        'result': 'PASS',
        'duration_seconds': round(time.monotonic() - started, 3),
        'apps': proof,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error))
        raise SystemExit(1)
