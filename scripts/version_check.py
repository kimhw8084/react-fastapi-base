#!/usr/bin/env python3
"""Verify that published version metadata agrees with the single VERSION source."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
if not re.fullmatch(r'\d+\.\d+\.\d+-(?:alpha|beta|rc)\.\d+', VERSION):
    raise SystemExit(f'Unsupported release version: {VERSION!r}')

frontend = json.loads((ROOT / 'frontend/package.json').read_text())
if frontend['version'] != VERSION:
    raise SystemExit('frontend/package.json does not match VERSION')

pyproject = (ROOT / 'backend/pyproject.toml').read_text()
pep440 = VERSION.replace('-rc.', 'rc').replace('-alpha.', 'a').replace('-beta.', 'b')
if f'version = "{pep440}"' not in pyproject:
    raise SystemExit('backend/pyproject.toml does not match VERSION')

print(f'Version metadata is synchronized at {VERSION}.')
