from __future__ import annotations

from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parents[3] / 'VERSION'
VERSION = _VERSION_FILE.read_text(encoding='utf-8').strip()

if not VERSION:
    raise RuntimeError('VERSION must not be empty.')

# API compatibility is deliberately independent from application semver. This
# is the single repository-owned source for the public API family and revision.
API_MAJOR = 1
API_CONTRACT_REVISION = 1
API_PREFIX = f'/api/v{API_MAJOR}'

if API_MAJOR < 1 or API_CONTRACT_REVISION < 1:
    raise RuntimeError('API contract metadata must use positive values.')
