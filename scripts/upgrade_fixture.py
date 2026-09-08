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
import tempfile
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / 'backend/.venv/bin/python'


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/release/upgrade-fixture.json')
    args = parser.parse_args()
    tools = load_template_tools()
    results: list[dict] = []
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix='react-fastapi-upgrade-') as raw:
        temp = Path(raw)
        old = temp / 'old-generated-app'
        incoming = temp / 'new-platform'
        tools.create_application(ROOT, old, 'upgrade-fixture', 'Upgrade Fixture')
        tools.create_application(ROOT, incoming, 'incoming-platform', 'Incoming Platform', 'clarity')

        managed = 'backend/app/platform/errors.py'
        path = incoming / managed
        path.write_text(path.read_text() + '\n# deterministic upgrade fixture change\n')
        before = tools.core_manifest(old)
        plan = tools.upgrade_plan(old, incoming)
        results.append({'name': 'upgrade-plan', 'exit_code': 0 if plan['conflicts'] == 0 else 1, 'plan_hash': plan['plan_hash'], 'changes': len(plan['changes']), 'conflicts': plan['conflicts']})
        if plan['conflicts']:
            raise RuntimeError('Generated upgrade fixture unexpectedly contains conflicts.')

        journal = tools.upgrade_apply(old, incoming, plan['plan_hash'], 'APP-STOPPED')
        results.append({'name': 'upgrade-apply', 'exit_code': 0, 'journal': os.path.relpath(journal, old)})
        if (old / managed).read_bytes() != (incoming / managed).read_bytes():
            raise RuntimeError('Upgrade apply did not install the planned managed file.')

        data_root = temp / 'database'
        tenant_id = str(uuid4())
        env = os.environ.copy()
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

    report = {
        'schema_version': 1,
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'command': ['python3', 'scripts/upgrade_fixture.py'],
        'exit_code': 0,
        'environment': {'platform': os.uname().sysname, 'machine': os.uname().machine},
        'hashes': {'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()},
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
