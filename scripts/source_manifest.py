"""Canonical executable-source hash set used by release verification."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORIES = ('backend', 'frontend', 'contracts', 'scripts', 'tests', 'experience-lab', 'catalog')
EXCLUDED_PARTS = {'__pycache__', '.pytest_cache', '.venv', 'venv', 'node_modules', 'dist', 'coverage', 'test-results', 'playwright-report'}
EXCLUDED_PATH_PREFIXES = {'frontend/public/experience-lab/', 'frontend/storybook-static/'}
EXCLUDED_NAMES = {'.coverage', 'coverage.xml'}
EXCLUDED_SUFFIXES = {'.pyc', '.log', '.sqlite3'}


def is_source_path(relative: Path) -> bool:
    if relative.as_posix() == 'dev':
        return True
    if not relative.parts or relative.parts[0] not in SOURCE_DIRECTORIES:
        return False
    if set(relative.parts) & EXCLUDED_PARTS:
        return False
    if any(relative.as_posix().startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
        return False
    if relative.name in EXCLUDED_NAMES or relative.suffix in EXCLUDED_SUFFIXES:
        return False
    return True


def source_hashes(root: Path = ROOT) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for directory in SOURCE_DIRECTORIES:
        directory_path = root / directory
        if not directory_path.is_dir():
            continue
        for path in sorted(directory_path.rglob('*')):
            relative = path.relative_to(root)
            if path.is_symlink() and is_source_path(relative):
                raise ValueError('Executable source includes a symlinked path; refusing to hash content outside the checkout.')
            if path.is_file() and is_source_path(relative):
                hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    dev = root / 'dev'
    if dev.is_file():
        hashes['dev'] = hashlib.sha256(dev.read_bytes()).hexdigest()
    return hashes


def source_digest(hashes: dict[str, str] | None = None) -> str:
    values = source_hashes() if hashes is None else hashes
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def checkout_commit(root: Path = ROOT) -> str:
    result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError('The checkout commit is unavailable.')
    return result.stdout.strip()


def executable_source_commit(root: Path = ROOT) -> str:
    result = subprocess.run(
        ['git', 'log', '-1', '--format=%H', '--', *SOURCE_DIRECTORIES, 'dev'],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError('The executable-source commit is unavailable.')
    return result.stdout.strip()


def source_provenance(root: Path = ROOT) -> dict[str, str]:
    """Return the canonical identity used by source-bound repository evidence.

    ``checkout_commit`` is the exact candidate/evidence checkout.  It may be
    newer than ``executable_source_commit`` when a commit only adds evidence
    or release binding metadata.  The digest is calculated from the canonical
    executable-source hash set, never from generated evidence or local state.
    """
    hashes = source_hashes(root)
    return {
        'checkout_commit': checkout_commit(root),
        'executable_source_commit': executable_source_commit(root),
        'source_digest': source_digest(hashes),
    }


def source_hashes_at_git(commit: str, *, root: Path = ROOT) -> dict[str, str]:
    result = subprocess.run(
        ['git', 'ls-tree', '-r', '--name-only', commit],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or f'Unable to inspect source base {commit}.')
    hashes: dict[str, str] = {}
    for name in result.stdout.splitlines():
        relative = Path(name)
        if not is_source_path(relative):
            continue
        blob = subprocess.run(
            ['git', 'show', f'{commit}:{name}'],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if blob.returncode != 0:
            raise ValueError(blob.stderr.decode(errors='replace').strip() or f'Unable to read source base path {name}.')
        hashes[name] = hashlib.sha256(blob.stdout).hexdigest()
    return hashes
