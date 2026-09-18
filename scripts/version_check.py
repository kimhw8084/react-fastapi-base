#!/usr/bin/env python3
"""Verify version metadata and, when requested, exact-base progression."""
from __future__ import annotations

import json
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_version import (
    ReleaseProgressionError,
    ReleaseVersionError,
    assert_candidate_progression,
    read_candidate_version,
)


def check_metadata(root: Path = ROOT) -> str:
    version = read_candidate_version(root)
    frontend = json.loads((root / 'frontend/package.json').read_text(encoding='utf-8'))
    if frontend['version'] != version.version:
        raise ReleaseVersionError('frontend/package.json does not match VERSION')

    package_lock = json.loads((root / 'frontend/package-lock.json').read_text(encoding='utf-8'))
    if package_lock.get('version') != version.version or package_lock.get('packages', {}).get('', {}).get('version') != version.version:
        raise ReleaseVersionError('frontend/package-lock.json root metadata does not match VERSION')

    pyproject = (root / 'backend/pyproject.toml').read_text(encoding='utf-8')
    if f'version = "{version.pep440}"' not in pyproject:
        raise ReleaseVersionError('backend/pyproject.toml does not match VERSION')
    return version.version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-sha', default=os.environ.get('RELEASE_BASE_SHA') or os.environ.get('API_COMPATIBILITY_BASE_SHA'))
    parser.add_argument('--stable-promotion', action='store_true')
    args = parser.parse_args()
    version = check_metadata()
    if args.base_sha:
        result = assert_candidate_progression(
            base_sha=args.base_sha,
            root=ROOT,
            candidate_version=version,
            stable_promotion=args.stable_promotion,
        )
        print(json.dumps({'version': version, 'progression': result.as_dict()}, sort_keys=True))
    else:
        print(f'Version metadata is synchronized at {version}.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, KeyError, json.JSONDecodeError, ReleaseVersionError, ReleaseProgressionError) as error:
        print(f'Version/progression check FAILED: {error}')
        raise SystemExit(1) from None
