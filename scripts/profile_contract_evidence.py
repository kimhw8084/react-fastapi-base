#!/usr/bin/env python3
"""Record source-bound CHG-27 profile-contract verification."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'evidence/current/release/CHG-27-profile-contract.json'
SOURCE_FILES = (
    'VERSION',
    'backend/app/main.py',
    'backend/app/platform/identity.py',
    'backend/app/platform/profile.py',
    'backend/app/platform/provision.py',
    'backend/app/platform/security.py',
    'backend/app/platform/storage.py',
    'backend/app/platform/router.py',
    'backend/app/tooling/work_items.py',
    'backend/app/cli.py',
    'backend/app/profiles/loader.py',
    'backend/app/profiles/storage.py',
    'backend/app/profiles/scanner.py',
    'backend/app/profiles/company/deployment.py',
    'backend/app/profiles/company/identity.py',
    'backend/app/profiles/company/profile.py',
    'backend/app/profiles/company/storage.py',
    'backend/app/profiles/development/deployment.py',
    'backend/app/profiles/development/identity.py',
    'backend/app/profiles/development/profile.py',
    'backend/app/profiles/development/storage.py',
    'backend/tests/test_profiles.py',
    'frontend/public/runtime-config.json',
    'frontend/tests/server.test.mjs',
    'scripts/check_architecture.py',
)


def source_binding() -> tuple[str, str, dict[str, str]]:
    files = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE_FILES}
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    digest = hashlib.sha256(json.dumps({'head': head, 'files': files}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return head, digest, files


def run_check(name: str, command: list[str], cwd: Path) -> dict[str, object]:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        return {
            'name': name,
            'status': 'PASS' if result.returncode == 0 else 'FAIL',
            'command': command,
            'cwd': str(cwd.relative_to(ROOT)),
            'exit_code': result.returncode,
            'output_tail': result.stdout[-4000:],
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'name': name, 'status': 'BLOCKED', 'command': command, 'cwd': str(cwd.relative_to(ROOT)), 'reason': str(error)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    head, digest, files = source_binding()
    checks = [
        run_check('profile-and-security-tests', [sys.executable, '-m', 'pytest', '-q', 'tests/test_profiles.py', 'tests/test_security.py'], ROOT / 'backend'),
        run_check('architecture', [sys.executable, 'scripts/check_architecture.py'], ROOT),
        run_check('public-runtime-boundary', ['node', '--test', 'frontend/tests/server.test.mjs'], ROOT),
    ]
    result = {
        'schema_version': 1,
        'project': 'react-fastapi-base',
        'change': 'CHG-27',
        'base_sha': '68b55ee1dd3fda00d8899682b4f8a09733f3dd0b',
        'accepted_chg6_sha': '3c20bcf12259daefb4024745e4974ce349de22a4',
        'version': (ROOT / 'VERSION').read_text(encoding='utf-8').strip(),
        'source_head': head,
        'candidate_source_digest': digest,
        'source_files': files,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'environment': {'platform': platform.platform(), 'python': platform.python_version()},
        'checks': checks,
        'result': 'PASS' if all(check['status'] == 'PASS' for check in checks) else 'FAIL',
        'production_ready': False,
        'note': 'The accepted CHG-6 RC.7 commit is preserved unchanged in ancestry. This evidence binds the RC.8 candidate source to source_head plus candidate_source_digest; it does not certify company identity, storage, deployment or production readiness.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"{result['result']} — report: {args.output}")
    return 0 if result['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
