#!/usr/bin/env python3
"""Run a clean, cache-isolated Mac clone certification for local release gates."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/release/fresh-clone-macos.json')
    args = parser.parse_args()
    commands = [
        ['git', 'clone', '--branch', 'main', '--single-branch', 'https://github.com/kimhw8084/react-fastapi-base.git', 'clone'],
        ['python3', 'dev', 'setup'],
        ['python3', 'dev', 'contracts'],
        ['python3', 'dev', 'architecture'],
        ['python3', 'scripts/catalog.py', '--check', '--release'],
        ['.venv/bin/python', '-m', 'pytest', '-q'],
        ['npm', 'run', 'typecheck'],
        ['npm', 'run', 'build'],
        ['npm', 'run', 'build:storybook'],
        ['npx', 'playwright', 'install', 'chromium'],
        ['python3', 'scripts/e2e_runner.py'],
    ]
    results = []
    started = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(prefix='react-fastapi-base-macos-clean-') as temporary:
        folder = Path(temporary)
        clone = folder / 'clone'
        environment = {key: value for key, value in os.environ.items() if not key.startswith('BASE_') and key not in {'AccessKey', 'PIP_CACHE_DIR', 'npm_config_cache'}}
        environment.update(PIP_NO_CACHE_DIR='1', npm_config_cache=str(folder / 'npm-cache'), PLAYWRIGHT_BROWSERS_PATH=str(folder / 'browsers'))
        node_bins = [path for path in (Path.home() / '.nvm/versions/node').glob('v22*/bin') if (path / 'node').is_file()]
        if node_bins:
            environment['PATH'] = f"{sorted(node_bins)[-1]}:{environment.get('PATH', '')}"
        node_path = shutil.which('node', path=environment.get('PATH'))
        if not node_path or not subprocess.check_output([node_path, '--version'], text=True).strip().startswith('v22.'):
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({'schema_version': 1, 'platform': platform.platform(), 'result': 'FAIL', 'reason': 'Node 22 is required for the locked frontend.'}, indent=2) + '\n')
            return 1
        preinstall_clean = True
        for index, command in enumerate(commands):
            cwd = folder if index == 0 else clone
            if command[0] in {'npm', 'npx'}: cwd = clone / 'frontend'
            if command[0] == '.venv/bin/python': cwd = clone / 'backend'
            if command[0] == 'python3' and len(command) > 2 and command[1] == 'scripts/e2e_runner.py': cwd = clone
            if index == 1 and ((clone / 'backend/.venv').exists() or (clone / 'frontend/node_modules').exists()):
                preinstall_clean = False
                break
            try:
                completed = subprocess.run(command, cwd=cwd, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1200)
                output = completed.stdout[-12000:]
                results.append({'command': command, 'exit_code': completed.returncode, 'output': output})
                print(f"{completed.returncode:3} {' '.join(command)}", flush=True)
                if completed.returncode != 0:
                    break
            except (OSError, subprocess.TimeoutExpired) as error:
                results.append({'command': command, 'exit_code': None, 'error': str(error)})
                break
        report = {
            'schema_version': 1,
            'platform': platform.platform(),
            'macos': platform.system() == 'Darwin',
            'started_at': started.isoformat(),
            'finished_at': datetime.now(timezone.utc).isoformat(),
            'source': 'https://github.com/kimhw8084/react-fastapi-base.git',
            'isolated_temp_directory': True,
            'cache_isolated': True,
            'preinstall_clean': preinstall_clean,
            'commands': results,
            'result': 'PASS' if preinstall_clean and results and results[-1].get('exit_code') == 0 and len(results) == len(commands) and platform.system() == 'Darwin' else 'FAIL',
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
