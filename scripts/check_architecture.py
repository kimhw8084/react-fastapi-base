#!/usr/bin/env python3
"""Small, explicit structural checks; not a substitute for behavioral/security tests."""
import ast
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
errors=[]
for path in (ROOT/'backend/app').rglob('*.py'):
    source=path.read_text();tree=ast.parse(source,filename=str(path));relative=path.relative_to(ROOT).as_posix()
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            imports=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
            if '/platform/' in relative and any(name.startswith('app.features') for name in imports):errors.append(f'{relative}: platform imports a feature')
    if "os.environ.get('AccessKey')" in source and relative!='backend/app/profiles/company/identity.py':errors.append(f'{relative}: identity adapter bypass')
    if re.search(r'\b(?:eval|exec)\(',source):errors.append(f'{relative}: dynamic code execution')
for path in (ROOT/'frontend/src').rglob('*'):
    if path.suffix not in {'.ts','.tsx'}:continue
    source=path.read_text();relative=path.relative_to(ROOT).as_posix()
    if path.name.endswith(('.test.ts','.test.tsx')) or '/generated/' in relative:continue
    if '/platform/' in relative and re.search(r"from\s+['\"][^'\"]*(?:/features/|/app/)",source):errors.append(f'{relative}: platform imports application code')
    if re.search(r'\bfetch\(',source) and relative not in {'frontend/src/platform/api/client.ts','frontend/src/platform/api/runtime.ts'}:errors.append(f'{relative}: raw fetch outside transport')
    if re.search(r'\blocalStorage\.',source) and relative!='frontend/src/platform/state/storage.ts':errors.append(f'{relative}: unscoped local storage')
    if '/features/' in relative and re.search(r'#[0-9a-fA-F]{6}\b',source):errors.append(f'{relative}: raw feature color; use semantic tokens')
    if re.search(r'\b(?:eval|new Function)\(',source):errors.append(f'{relative}: dynamic code execution')
for path in ROOT.rglob('*'):
    if not path.is_file() or set(path.relative_to(ROOT).parts)&{'.venv','.local','.evidence','node_modules','__pycache__','.git'}:continue
    if path.name in {'.env','.env.local'}:errors.append(f'{path.relative_to(ROOT)}: real environment file must not ship')
config=json.loads((ROOT/'backend/app/config/application.json').read_text())
manifest=json.loads((ROOT/'backend/app/features/manifest.json').read_text())
if not {x['workspace'] for x in config['navigation']}<=set(manifest):errors.append('Navigation references an unregistered feature.')
if errors:raise SystemExit('\n'.join(errors))
print('Architecture checks passed: dependency direction, transport, storage, identity ownership and source hygiene.')
