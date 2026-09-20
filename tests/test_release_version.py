from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.release_version import (
    ReleaseVersionError,
    check_candidate_progression,
    compare_stable_version_projection,
    parse_candidate_version,
    release_paths,
)
from scripts.source_manifest import executable_source_commit


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
    assert executable_source_commit(repo) == base


def test_stacked_candidate_requires_contiguous_preserved_prerelease_ancestry(tmp_path: Path):
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

    (repo / 'VERSION').write_text('1.0.0-rc.13\n')
    (repo / 'backend/source.py').write_text('VALUE = 2\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'preserved intermediate candidate')
    (repo / 'VERSION').write_text('1.0.0-rc.14\n')
    (repo / 'backend/source.py').write_text('VALUE = 3\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'stacked candidate')

    result = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0-rc.14')
    assert result.allowed is True
    assert result.mode == 'stacked_ordinary_build'

    (repo / 'VERSION').write_text('1.0.0-rc.16\n')
    assert check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0-rc.16').allowed is False


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def _stable_projection_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / 'repo'
    repo.mkdir()
    (repo / 'VERSION').write_text('1.0.0-rc.13\n')
    _write_json(repo / 'frontend/package.json', {
        'name': 'fixture-frontend',
        'version': '1.0.0-rc.13',
        'private': True,
        'type': 'module',
        'scripts': {'build': 'vite build'},
        'dependencies': {'react': '18.3.1'},
        'devDependencies': {'vitest': '4.1.11'},
    })
    _write_json(repo / 'frontend/package-lock.json', {
        'name': 'fixture-frontend',
        'version': '1.0.0-rc.13',
        'lockfileVersion': 3,
        'requires': True,
        'packages': {
            '': {
                'name': 'fixture-frontend',
                'version': '1.0.0-rc.13',
                'dependencies': {'react': '18.3.1'},
                'devDependencies': {'vitest': '4.1.11'},
            },
            'node_modules/react': {
                'version': '18.3.1',
                'resolved': 'https://registry.npmjs.org/react/-/react-18.3.1.tgz',
                'integrity': 'sha512-fixture',
            },
        },
    })
    (repo / 'backend/pyproject.toml').parent.mkdir(parents=True, exist_ok=True)
    (repo / 'backend/pyproject.toml').write_text(
        '[project]\n'
        'name = "fixture-backend"\n'
        'version = "1.0.0rc13"\n'
        'requires-python = ">=3.11,<3.15"\n'
        'dependencies = ["fastapi==0.141.1"]\n'
    )
    _write_json(repo / 'contracts/openapi.json', {
        'openapi': '3.1.0',
        'info': {'title': 'Fixture API', 'version': '1.0.0-rc.13'},
        'paths': {'/health': {'get': {'operationId': 'health'}}},
        'components': {'schemas': {'Health': {'type': 'object'}}},
    })
    (repo / 'backend/runtime.py').parent.mkdir(parents=True, exist_ok=True)
    (repo / 'backend/runtime.py').write_text('VALUE = 1\n')
    (repo / 'frontend/src/runtime.ts').parent.mkdir(parents=True, exist_ok=True)
    (repo / 'frontend/src/runtime.ts').write_text('export const value = 1\n')
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 'release-test@example.invalid')
    git(repo, 'config', 'user.name', 'Release progression test')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'release candidate')
    base = git(repo, 'rev-parse', 'HEAD')

    (repo / 'VERSION').write_text('1.0.0\n')
    package = json.loads((repo / 'frontend/package.json').read_text())
    package['version'] = '1.0.0'
    _write_json(repo / 'frontend/package.json', package)
    lock = json.loads((repo / 'frontend/package-lock.json').read_text())
    lock['version'] = '1.0.0'
    lock['packages']['']['version'] = '1.0.0'
    _write_json(repo / 'frontend/package-lock.json', lock)
    pyproject = (repo / 'backend/pyproject.toml').read_text().replace('1.0.0rc13', '1.0.0')
    (repo / 'backend/pyproject.toml').write_text(pyproject)
    contract = json.loads((repo / 'contracts/openapi.json').read_text())
    contract['info']['version'] = '1.0.0'
    _write_json(repo / 'contracts/openapi.json', contract)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'explicit stable promotion')
    return repo, base


def test_stable_promotion_is_explicit_and_allows_real_version_projection(tmp_path: Path):
    repo, base = _stable_projection_repo(tmp_path)

    ordinary = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0')
    assert ordinary.allowed is False
    promoted = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0', stable_promotion=True)
    assert promoted.allowed is True
    assert promoted.source_changed is True
    assert promoted.version_projection_only is True
    assert promoted.as_dict()['version_projection_only'] is True
    projection = compare_stable_version_projection(
        base_sha=base,
        root=repo,
        previous=parse_candidate_version('1.0.0-rc.13'),
        candidate=parse_candidate_version('1.0.0'),
    )
    assert projection.allowed is True
    assert projection.changed_paths == (
        'backend/pyproject.toml',
        'contracts/openapi.json',
        'frontend/package-lock.json',
        'frontend/package.json',
    )
    assert set(projection.projection_fields) == {
        'backend/pyproject.toml:project.version',
        'contracts/openapi.json:info.version',
        "frontend/package-lock.json:packages[''].version",
        'frontend/package-lock.json:version',
        'frontend/package.json:version',
    }


@pytest.mark.parametrize('mutation', [
    'package_dependency',
    'lock_resolved',
    'lock_integrity',
    'lock_dependency',
    'pyproject_dependency',
    'backend_code',
    'frontend_code',
    'openapi_route',
    'additional_source',
])
def test_stable_promotion_rejects_each_non_version_mutation(tmp_path: Path, mutation: str):
    repo, base = _stable_projection_repo(tmp_path)

    if mutation == 'package_dependency':
        path = repo / 'frontend/package.json'
        document = json.loads(path.read_text())
        document['dependencies']['react'] = '18.3.2'
        _write_json(path, document)
    elif mutation == 'lock_resolved':
        path = repo / 'frontend/package-lock.json'
        document = json.loads(path.read_text())
        document['packages']['node_modules/react']['resolved'] += '?changed'
        _write_json(path, document)
    elif mutation == 'lock_integrity':
        path = repo / 'frontend/package-lock.json'
        document = json.loads(path.read_text())
        document['packages']['node_modules/react']['integrity'] = 'sha512-mutated'
        _write_json(path, document)
    elif mutation == 'lock_dependency':
        path = repo / 'frontend/package-lock.json'
        document = json.loads(path.read_text())
        document['packages']['']['dependencies']['react'] = '18.3.2'
        _write_json(path, document)
    elif mutation == 'pyproject_dependency':
        path = repo / 'backend/pyproject.toml'
        path.write_text(path.read_text().replace('fastapi==0.141.1', 'fastapi==0.141.2'))
    elif mutation == 'backend_code':
        (repo / 'backend/runtime.py').write_text('VALUE = 2\n')
    elif mutation == 'frontend_code':
        (repo / 'frontend/src/runtime.ts').write_text('export const value = 2\n')
    elif mutation == 'openapi_route':
        path = repo / 'contracts/openapi.json'
        document = json.loads(path.read_text())
        document['paths']['/mutated'] = {'get': {'operationId': 'mutated'}}
        _write_json(path, document)
    else:
        (repo / 'backend/unexpected.py').write_text('UNEXPECTED = True\n')

    substituted = check_candidate_progression(base_sha=base, root=repo, candidate_version='1.0.0', stable_promotion=True)
    assert substituted.allowed is False
    assert substituted.version_projection_only is False
    assert 'source' in substituted.reason.casefold() or 'metadata' in substituted.reason.casefold()


@pytest.mark.parametrize('mutation', ['missing_package_version', 'missing_lock_root_version', 'malformed_pyproject'])
def test_stable_promotion_rejects_malformed_or_incomplete_projection(tmp_path: Path, mutation: str):
    repo, base = _stable_projection_repo(tmp_path)

    if mutation == 'missing_package_version':
        path = repo / 'frontend/package.json'
        document = json.loads(path.read_text())
        del document['version']
        _write_json(path, document)
    elif mutation == 'missing_lock_root_version':
        path = repo / 'frontend/package-lock.json'
        document = json.loads(path.read_text())
        del document['packages']['']['version']
        _write_json(path, document)
    else:
        (repo / 'backend/pyproject.toml').write_text('[project\nversion = "1.0.0"\n')

    result = check_candidate_progression(
        base_sha=base,
        root=repo,
        candidate_version='1.0.0',
        stable_promotion=True,
    )
    assert result.allowed is False
    assert result.version_projection_only is False


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
