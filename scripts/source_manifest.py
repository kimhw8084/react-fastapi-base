"""Canonical executable-source hash set used by release verification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORIES = ('backend', 'frontend', 'contracts', 'scripts', 'tests', 'experience-lab', 'catalog')
EXCLUDED_PARTS = {'__pycache__', '.pytest_cache', '.venv', 'venv', 'node_modules', 'dist', 'coverage', 'test-results', 'playwright-report'}
EXCLUDED_NAMES = {'.coverage', 'coverage.xml'}
EXCLUDED_SUFFIXES = {'.pyc', '.log', '.sqlite3'}


def source_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for directory in SOURCE_DIRECTORIES:
        for path in sorted((ROOT / directory).rglob('*')):
            relative = path.relative_to(ROOT)
            if (
                path.is_file()
                and not set(relative.parts) & EXCLUDED_PARTS
                and path.name not in EXCLUDED_NAMES
                and path.suffix not in EXCLUDED_SUFFIXES
            ):
                hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    hashes['dev'] = hashlib.sha256((ROOT / 'dev').read_bytes()).hexdigest()
    return hashes


def source_digest(hashes: dict[str, str] | None = None) -> str:
    values = source_hashes() if hashes is None else hashes
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
