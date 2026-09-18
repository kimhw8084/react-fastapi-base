#!/usr/bin/env python3
"""Finalize a verified repository release candidate in deterministic order."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_version import current_release_paths


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def finalize(verification_path: Path, *, stable_promotion: bool = False) -> None:
    """Bind the final identity, then regenerate and verify the broad snapshot."""
    # Resolve the candidate paths before invoking the generator so finalization
    # cannot silently fall back to a historical release label.
    current_release_paths(ROOT)
    identity_command = [
        sys.executable,
        'scripts/generate_release_identity.py',
        '--verification',
        str(verification_path.resolve()),
        '--replace',
    ]
    if stable_promotion:
        identity_command.append('--stable-promotion')
    run([
        *identity_command,
    ])
    run([sys.executable, 'scripts/generate_checkpoint_manifest.py'])
    run([sys.executable, 'scripts/generate_checkpoint_manifest.py', '--check'])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--verification',
        type=Path,
        default=ROOT / 'evidence/current/full-stack/verification.json',
    )
    parser.add_argument('--stable-promotion', action='store_true')
    args = parser.parse_args()
    finalize(args.verification, stable_promotion=args.stable_promotion)
    print('Release finalization complete: identity, checkpoint, checkpoint check.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f'Release finalization FAILED: {error}', file=sys.stderr)
        raise SystemExit(1) from None
