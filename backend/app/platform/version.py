from __future__ import annotations

from pathlib import Path

_VERSION_FILE = Path(__file__).resolve().parents[3] / 'VERSION'
VERSION = _VERSION_FILE.read_text(encoding='utf-8').strip()

if not VERSION:
    raise RuntimeError('VERSION must not be empty.')
