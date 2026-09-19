from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.reusable_platform_qualification import _validate_source_binding
from scripts.source_manifest import source_provenance


ROOT = Path(__file__).resolve().parents[1]


def git(root: Path, *args: str) -> str:
    result = subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def test_source_provenance_distinguishes_evidence_only_checkout(tmp_path: Path) -> None:
    repo = tmp_path / 'repo'
    (repo / 'backend').mkdir(parents=True)
    (repo / 'evidence').mkdir()
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 'qualification@example.invalid')
    git(repo, 'config', 'user.name', 'Qualification test')
    (repo / 'backend' / 'source.py').write_text('VALUE = 1\n', encoding='utf-8')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'executable source')
    source = source_provenance(repo)
    (repo / 'evidence' / 'binding.json').write_text('{}\n', encoding='utf-8')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'evidence only')
    evidence = source_provenance(repo)
    assert evidence['checkout_commit'] != source['checkout_commit']
    assert evidence['executable_source_commit'] == source['executable_source_commit']
    assert evidence['source_digest'] == source['source_digest']


def test_evidence_binding_accepts_newer_checkout_when_source_is_exact() -> None:
    problems: list[str] = []
    _validate_source_binding(
        {
            'checkout_commit': 'b' * 40,
            'candidate_head': 'b' * 40,
            'executable_source_commit': 'a' * 40,
            'source_commit': 'a' * 40,
            'source_digest': 'c' * 64,
            'hashes': {'source_digest': 'c' * 64},
            'result': 'PASS',
            'exit_code': 0,
        },
        label='evidence-only',
        expected_commit='a' * 40,
        expected_digest='c' * 64,
        problems=problems,
    )
    assert problems == []


def test_documentation_and_command_contract_matches_current_dev_entrypoint() -> None:
    from scripts.reusable_platform_qualification import _validate_documentation

    problems: list[str] = []
    _validate_documentation((ROOT / 'VERSION').read_text(encoding='utf-8').strip(), problems)
    assert problems == []
