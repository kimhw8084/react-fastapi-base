from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from scripts.release_version import (
    ReleaseVersionError,
    check_candidate_progression,
    parse_candidate_version,
    release_paths,
)


ROOT = Path(__file__).resolve().parents[1]


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(['git', *args], cwd=repo, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


def test_current_candidate_paths_and_explicit_stable_label():
    paths = release_paths('1.0.0-rc.13', ROOT)
    assert paths.identity == ROOT / 'deploy/rc13-release-identity.json'
    assert paths.readiness_matrix == ROOT / 'evidence/current/release/rc13-readiness-matrix.json'
    assert paths.manifest == ROOT / 'evidence/current/release/rc13-manifest.json'
    assert paths.evidence_binding == ROOT / 'evidence/current/release/rc13-evidence-binding.json'

    stable = release_paths('1.0.0', ROOT)
    assert stable.identity == ROOT / 'deploy/stable-1.0.0-release-identity.json'
    assert stable.readiness_matrix == ROOT / 'evidence/current/release/stable-1.0.0-readiness-matrix.json'


@pytest.mark.parametrize('value', [
    '', '1', '1.0', 'v1.0.0', '1.0.0-rc', '1.0.0-rc.01', '01.0.0-rc.1',
    '1.0.0-rc.1+build', '1.0.0-alpha.1.beta.1',
])
def test_malformed_versions_are_rejected(value: str):
    with pytest.raises(ReleaseVersionError):
        parse_candidate_version(value)


def test_progression_rejects_reused_base_after_source_change(tmp_path: Path):
    repo = tmp_path / 'repo'
    (repo / 'backend').mkdir(parents=True)
    (repo / 'VERSION').write_text('1.0.0-rc.12\n')
    (repo / 'backend/source.py').write_text('VALUE = 1\n')
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 'release-test@example.invalid')
    git(repo, 'config', 'user.name', 'Release progression test')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'base candidate')
    base = git(repo, 'rev-parse', 'HEAD')

    (repo / 'backend/source.py').write_text('VALUE = 2\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'changed source')
    reused = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0-rc.12')
    assert reused.allowed is False
    assert 'reuse' not in reused.reason.casefold() or 'exactly' in reused.reason.casefold()

    advanced = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0-rc.13')
    assert advanced.allowed is True
    assert advanced.source_changed is True

    rolled_back = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0-rc.11')
    assert rolled_back.allowed is False


def test_evidence_only_commit_may_retain_established_candidate(tmp_path: Path):
    repo = tmp_path / 'repo'
    (repo / 'backend').mkdir(parents=True)
    (repo / 'VERSION').write_text('1.0.0-rc.13\n')
    (repo / 'backend/source.py').write_text('VALUE = 1\n')
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 'release-test@example.invalid')
    git(repo, 'config', 'user.name', 'Release progression test')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'established candidate')
    base = git(repo, 'rev-parse', 'HEAD')
    (repo / 'evidence.txt').write_text('binding evidence\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'evidence binding')
    result = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0-rc.13')
    assert result.allowed is True
    assert result.mode == 'evidence_only'
    assert result.source_changed is False


def test_stable_promotion_is_explicit_and_rejects_source_substitution(tmp_path: Path):
    repo = tmp_path / 'repo'
    (repo / 'backend').mkdir(parents=True)
    (repo / 'VERSION').write_text('1.0.0-rc.13\n')
    (repo / 'backend/source.py').write_text('VALUE = 1\n')
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 'release-test@example.invalid')
    git(repo, 'config', 'user.name', 'Release progression test')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'release candidate')
    base = git(repo, 'rev-parse', 'HEAD')
    (repo / 'VERSION').write_text('1.0.0\n')
    git(repo, 'add', 'VERSION')
    git(repo, 'commit', '-qm', 'explicit stable promotion')

    ordinary = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0')
    assert ordinary.allowed is False
    promoted = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0', stable_promotion=True)
    assert promoted.allowed is True

    (repo / 'backend/source.py').write_text('VALUE = 2\n')
    substituted = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0', stable_promotion=True)
    assert substituted.allowed is False
    assert 'substitution' in substituted.reason


def test_historical_release_artifact_hashes_are_unchanged():
    expected = {
        'deploy/rc11-release-identity.json': 'ce9b8bc8b4204c5eab89630194cdea538bb3b3c81788ce0982322735167c1601',
        'deploy/rc12-release-identity.json': '3d0f98e5bebbc5e52c8f2e129a9a21cfd212d6ff2148f5974ac64d1491c4488e',
        'evidence/current/release/rc11-readiness-matrix.json': '9af66bd4078d7bb0ff7cf43a8029506aefa6cc2ef9f716d73c5483d3e81e7994',
        'evidence/current/release/rc11-manifest.json': 'f19feacd5593f4e0855e47192e457380066806949f84ae606b9193150edcd10a',
        'evidence/current/release/rc11-evidence-binding.json': '057d2c594a560d47ac065b5f6efe34d749aede49cc93a49d6a8aa2ca1a7fca73',
        'evidence/current/release/rc12-readiness-matrix.json': 'b900e6c3ecbc6621471284ffbd3ac1a7ff77f639b8ff051f76e2e83fcffd07af',
        'evidence/current/release/rc12-manifest.json': '7a601c1d497072f0c5492054a3e605847a72dc308f56ef9dc524bec9bcce0120',
        'evidence/current/release/rc12-evidence-binding.json': 'bb9fe8d4ca31ea009570ee09d83dd8346c877a40ff7b76a61032e0d10e64fb93',
    }
    for relative in expected:
        path = ROOT / relative
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected[relative]
