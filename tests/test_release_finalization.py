from __future__ import annotations

import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_NAMES = (
    'source_manifest.py',
    'generate_checkpoint_manifest.py',
    'generate_release_identity.py',
    'finalize_release.py',
)


def run(repo: Path, *command: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    return result


def source_report(repo: Path) -> None:
    commit = run(repo, 'git', 'rev-parse', 'HEAD').stdout.strip()
    digest_result = run(
        repo,
        sys.executable,
        '-c',
        'import json, sys; sys.path.insert(0, "scripts"); '
        'from source_manifest import source_digest, source_hashes; '
        'print(json.dumps({"digest": source_digest(), "hashes": source_hashes()}))',
    )
    values = json.loads(digest_result.stdout)
    evidence = repo / 'evidence/current/full-stack'
    (evidence / 'source-hashes.json').write_text(
        json.dumps(values['hashes'], indent=2) + '\n',
        encoding='utf-8',
    )
    (evidence / 'verification.json').write_text(
        json.dumps({
            'code_ready': True,
            'source_commit': commit,
            'source_digest': values['digest'],
            'source_hashes': 'source-hashes.json',
        }) + '\n',
        encoding='utf-8',
    )


def test_finalization_repairs_identity_checkpoint_ordering(tmp_path: Path) -> None:
    repo = tmp_path / 'repo'
    (repo / 'scripts').mkdir(parents=True)
    for directory in ('backend', 'frontend', 'contracts', 'tests', 'experience-lab', 'catalog', 'deploy', 'evidence/current/full-stack'):
        (repo / directory).mkdir(parents=True, exist_ok=True)
    (repo / 'dev').write_text('#!/usr/bin/env python3\n', encoding='utf-8')
    (repo / 'VERSION').write_text('1.0.0-rc.12\n', encoding='utf-8')
    (repo / 'backend/source.py').write_text('VALUE = 1\n', encoding='utf-8')
    for name in SCRIPT_NAMES:
        shutil.copy2(ROOT / 'scripts' / name, repo / 'scripts' / name)

    run(repo, 'git', 'init', '-q')
    run(repo, 'git', 'config', 'user.email', 'test@example.invalid')
    run(repo, 'git', 'config', 'user.name', 'Release finalization test')
    run(repo, 'git', 'add', '.')
    run(repo, 'git', 'commit', '-qm', 'initial source')
    source_report(repo)
    verification = 'evidence/current/full-stack/verification.json'
    run(repo, sys.executable, 'scripts/generate_release_identity.py', '--verification', verification)
    run(repo, sys.executable, 'scripts/generate_checkpoint_manifest.py')

    (repo / 'backend/source.py').write_text('VALUE = 2\n', encoding='utf-8')
    run(repo, 'git', 'add', 'backend/source.py')
    run(repo, 'git', 'commit', '-qm', 'new verified source')
    source_report(repo)
    # Establish a current snapshot for the new executable source while the old identity remains.
    run(repo, sys.executable, 'scripts/generate_checkpoint_manifest.py')
    run(repo, sys.executable, 'scripts/generate_release_identity.py', '--verification', verification, '--replace')
    stale = run(repo, sys.executable, 'scripts/generate_checkpoint_manifest.py', '--check', expected=1)
    assert 'Checkpoint manifest is stale' in stale.stdout

    run(repo, sys.executable, 'scripts/finalize_release.py', '--verification', verification)
    identity = repo / 'deploy/rc12-release-identity.json'
    manifest = json.loads((repo / 'CHECKPOINT_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['files']['deploy/rc12-release-identity.json'] == hashlib.sha256(identity.read_bytes()).hexdigest()
    run(repo, sys.executable, 'scripts/generate_checkpoint_manifest.py', '--check')

    rebound = json.loads(identity.read_text(encoding='utf-8'))
    rebound['source_digest'] = 'f' * 64
    identity.write_text(json.dumps(rebound, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    run(repo, sys.executable, 'scripts/generate_checkpoint_manifest.py', '--check', expected=1)
