#!/usr/bin/env python3
"""Deterministic repository security hygiene checks that require no network.

This is deliberately narrower than a dependency vulnerability scanner. It prevents
common source/release mistakes from being mislabeled as production-ready while
network-backed advisory gates remain separate in verify.py.
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {'.py','.ts','.tsx','.js','.mjs','.json','.yaml','.yml','.md','.toml','.ini','.cfg','.txt','.css','.html','.sh'}
PRIVATE_KEY_MARKERS = ('-----BEGIN '+'PRIVATE KEY-----','-----BEGIN '+'RSA PRIVATE KEY-----','-----BEGIN '+'OPENSSH PRIVATE KEY-----')
SECRET_PATTERNS = [
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'(?i)(?:api[_-]?key|secret[_-]?key|password)\s*[:=]\s*["\'][A-Za-z0-9+/=_-]{20,}["\']'),
]
ALLOWED_ACCESSKEY_READ = 'backend/app/profiles/company/identity.py'


def tracked_files() -> list[Path]:
    result = subprocess.run(['git','ls-files','-z'],cwd=ROOT,check=True,stdout=subprocess.PIPE)
    return [ROOT / raw.decode() for raw in result.stdout.split(b'\0') if raw]


def main() -> int:
    errors: list[str] = []
    files = tracked_files()
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        name = path.name.lower()
        if name == '.env' or (name.startswith('.env.') and not any(x in name for x in ('example','sample','template'))):
            errors.append(f'{rel}: tracked environment file is forbidden')
        if path.suffix.lower() in {'.pem','.p12','.pfx','.key'}:
            errors.append(f'{rel}: private credential/key material extension is forbidden')
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text('utf-8')
        except UnicodeDecodeError:
            continue
        if any(marker in text for marker in PRIVATE_KEY_MARKERS):
            errors.append(f'{rel}: private key marker found')
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f'{rel}: probable hard-coded credential found')
        if rel.startswith('backend/app/') and "os.environ.get('AccessKey')" in text and rel != ALLOWED_ACCESSKEY_READ:
            errors.append(f'{rel}: AccessKey may only be read by the company identity adapter')
        if 'dangerouslySetInnerHTML' in text and rel.startswith('frontend/src/'):
            errors.append(f'{rel}: raw HTML injection requires an explicit sanitized platform abstraction')
        if re.search(r'fetch\(\s*["\']https?://', text) and rel.startswith('frontend/src/'):
            errors.append(f'{rel}: frontend source must use the bounded API transport, not direct external fetch')
    # Production dependency inputs must use exact pins where this repository owns them.
    requirements = ROOT/'backend/requirements.lock'
    if not requirements.is_file():
        errors.append('backend/requirements.lock: missing locked backend dependencies')
    else:
        for number,line in enumerate(requirements.read_text().splitlines(),1):
            stripped=line.strip()
            if stripped and not stripped.startswith('#') and '==' not in stripped:
                errors.append(f'backend/requirements.lock:{number}: dependency is not exactly pinned')
    package = ROOT/'frontend/package.json'
    if package.is_file():
        import json
        data=json.loads(package.read_text())
        for group in ('dependencies','devDependencies'):
            for name,version in data.get(group,{}).items():
                if version.startswith(('^','~','>','<','*','workspace:')):
                    errors.append(f'frontend/package.json: {name} must be exactly pinned for production')
    if errors:
        print('Security source checks FAILED:')
        for error in errors: print(' - '+error)
        return 1
    print(f'Security source checks passed: {len(files)} tracked files inspected; no tracked secrets, identity bypasses, raw HTML injection, or unpinned owned dependencies detected.')
    return 0

if __name__=='__main__': raise SystemExit(main())
