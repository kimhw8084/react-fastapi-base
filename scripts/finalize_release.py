#!/usr/bin/env python3
"""Finalize a verified RC.12 source candidate in deterministic order."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def finalize(verification_path: Path) -> None:
    """Bind the final identity, then regenerate and verify the broad snapshot."""
    run([
        sys.executable,
        'scripts/generate_release_identity.py',
        '--verification',
        str(verification_path.resolve()),
        '--replace',
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
    args = parser.parse_args()
    finalize(args.verification)
    print('Release finalization complete: identity, checkpoint, checkpoint check.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f'Release finalization FAILED: {error}', file=sys.stderr)
        raise SystemExit(1) from None
