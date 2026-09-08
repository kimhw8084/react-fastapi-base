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
    env = os.environ.copy()
    env['PATH'] = str(node_bins[-1]) + os.pathsep + env.get('PATH', '')
    proof = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='react-fastapi-reference-apps-') as raw:
        root = Path(raw)
        for app_id, name, theme in APPS:
            app = root / app_id
            tools.create_application(ROOT, app, app_id, name, theme)
            config = json.loads((app / 'backend/app/config/application.json').read_text())
            runtime = json.loads((app / 'frontend/public/runtime-config.json').read_text())
            if config['id'] != app_id or config['name'] != name or runtime['titleOverride'] != name:
                raise RuntimeError(f'Generated configuration mismatch for {app_id}.')
            steps = []
            steps.append({'name': 'contracts', **run([str(PYTHON), 'scripts/generate_contracts.py'], app, {**env, 'BASE_ENVIRONMENT': 'test', 'BASE_PROFILE': 'development', 'PYTHONPATH': str(app / 'backend')})})
            for label, command in (('frontend-install', ['npm', 'ci', '--ignore-scripts']), ('frontend-typecheck', ['npm', 'run', 'typecheck']), ('frontend-tests', ['npm', 'test']), ('frontend-build', ['npm', 'run', 'build'])):
                steps.append({'name': label, **run(command, app / 'frontend', env)})
            if any(step['exit_code'] != 0 for step in steps):
                failed = next(step for step in steps if step['exit_code'] != 0)
                raise RuntimeError(f'Reference app proof failed for {app_id}: {failed}')
            proof.append({'id': app_id, 'name': name, 'theme': theme, 'steps': steps, 'template_lock': json.loads((app / 'template.lock.json').read_text())['platform_version']})
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    report = {'schema_version': 1, 'source_commit': source_commit, 'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'command': ['python3', 'scripts/reference_app_proof.py'], 'exit_code': 0, 'environment': {'platform': os.uname().sysname, 'machine': os.uname().machine}, 'hashes': {'source_commit': source_commit}, 'result': 'PASS', 'duration_seconds': round(time.monotonic() - started, 3), 'apps': proof}
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
