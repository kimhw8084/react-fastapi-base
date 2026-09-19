#!/usr/bin/env python3
"""Run a clean, cache-isolated exact-candidate install proof."""
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
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.source_manifest import source_provenance


DEVELOPMENT_BOOTSTRAP_CHECK = (
    "from fastapi.testclient import TestClient; "
    "from app.main import create_app; "
    "from app.platform.settings import Settings; "
    "from pathlib import Path; "
    "settings=Settings(environment='development', profile='development', "
    "data_root=Path('../.local/development'), dev_user='demo.admin'); "
    "app=create_app(settings); client=TestClient(app); "
    "payload=client.get('/api/v1/bootstrap').json(); "
    "assert payload['profile']=='development' and payload['user_id']=='demo.admin'; "
    "assert 'AccessKey' not in str(payload) and 'data_root' not in str(payload) and 'profile_runtime' not in str(payload); client.close()"
)


def verification_commands(source_root: Path, source_commit: str) -> list[list[str]]:
    return [
        ['git', 'clone', '--no-local', str(source_root), 'clone'],
        ['git', 'checkout', '--detach', source_commit],
        ['python3', 'dev', 'setup'],
        ['python3', 'dev', 'seed-demo'],
        ['.venv/bin/python', '-c', DEVELOPMENT_BOOTSTRAP_CHECK],
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


def platform_qualification(portable_pass: bool, platform_name: str) -> str:
    if not portable_pass:
        return 'FAIL'
    return 'PASS' if platform_name == 'Darwin' else 'BLOCKED'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/release/fresh-clone-macos.json')
    args = parser.parse_args()
    provenance = source_provenance(ROOT)
    candidate_head = provenance['checkout_commit']
    executable_source_commit = provenance['executable_source_commit']
    source_digest = provenance['source_digest']
    commands = verification_commands(ROOT, candidate_head)
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
            args.output.write_text(json.dumps({
                'schema_version': 3,
                'platform': platform.platform(),
                'candidate_head': candidate_head,
                'checkout_commit': candidate_head,
                'executable_source_commit': executable_source_commit,
                'source_digest': source_digest,
                'source_commit': executable_source_commit,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'command': commands,
                'exit_code': 1,
                'environment': {'platform': platform.platform(), 'profile': 'development'},
                'hashes': {'source_digest': source_digest},
                'profile': 'development',
                'result': 'FAIL',
                'reason': 'Node 22 is required for the locked frontend.',
            }, indent=2) + '\n')
            return 1
        preinstall_clean = True
        initial_runtime_paths = ('backend/.venv', 'frontend/node_modules', '.local', '.evidence')
        for index, command in enumerate(commands):
            cwd = folder if index == 0 else clone
            if command[0] in {'npm', 'npx'}: cwd = clone / 'frontend'
            if command[0] == '.venv/bin/python': cwd = clone / 'backend'
            if command[0] == 'python3' and len(command) > 2 and command[1] == 'scripts/e2e_runner.py': cwd = clone
            if command == ['python3', 'dev', 'setup'] and any((clone / path).exists() for path in initial_runtime_paths):
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
        cloned_provenance = source_provenance(clone) if clone.is_dir() and (clone / '.git').is_dir() else None
        cloned_candidate_head = cloned_provenance['checkout_commit'] if cloned_provenance else None
        cloned_executable_source_commit = cloned_provenance['executable_source_commit'] if cloned_provenance else None
        cloned_source_digest = cloned_provenance['source_digest'] if cloned_provenance else None
        portable_pass = (
            preinstall_clean
            and results
            and results[-1].get('exit_code') == 0
            and len(results) == len(commands)
            and cloned_candidate_head == candidate_head
            and cloned_executable_source_commit == executable_source_commit
            and cloned_source_digest == source_digest
        )
        exit_code = 0 if portable_pass else 1
        report = {
            'schema_version': 3,
            'platform': platform.platform(),
            'candidate_head': candidate_head,
            'checkout_commit': candidate_head,
            'cloned_candidate_head': cloned_candidate_head,
            'executable_source_commit': executable_source_commit,
            'cloned_executable_source_commit': cloned_executable_source_commit,
            'source_digest': source_digest,
            'cloned_source_digest': cloned_source_digest,
            'source_commit': executable_source_commit,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'command': commands,
            'exit_code': exit_code,
            'environment': {'platform': platform.platform(), 'node': node_path, 'python': platform.python_version()},
            'hashes': {'source_digest': source_digest},
            'profile': 'development',
            'credential_free': True,
            'default_runtime_non_secret': True,
            'macos': platform.system() == 'Darwin',
            'candidate_result': 'PASS' if portable_pass else 'FAIL',
            'macos_qualification': platform_qualification(portable_pass, platform.system()),
            'macos_qualification_reason': 'Executed on macOS.' if platform.system() == 'Darwin' else 'The portable exact-candidate proof ran; macOS-specific qualification requires a Darwin runner.',
            'started_at': started.isoformat(),
            'finished_at': datetime.now(timezone.utc).isoformat(),
            'source': 'current repository checkout at HEAD',
            'isolated_temp_directory': True,
            'cache_isolated': True,
            'preinstall_clean': preinstall_clean,
            'commands': results,
            'result': 'PASS' if exit_code == 0 else 'FAIL',
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
