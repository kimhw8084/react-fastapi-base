#!/usr/bin/env python3
"""Typecheck and verify shipped JS/declarations against a fresh TypeScript build."""
import hashlib,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    local=ROOT/'frontend/node_modules/.bin/tsc'
    tsc=str(local) if local.is_file() else shutil.which('tsc')
    if not tsc:raise SystemExit('BLOCKED: install the TypeScript compiler. Compiled Lab remains runnable.')
    with tempfile.TemporaryDirectory(prefix='rfb-lab-build-') as temp:
        subprocess.run([tsc,'-p',str(ROOT/'experience-lab/tsconfig.json'),'--outDir',temp],check=True)
        built=Path(temp);public=ROOT/'experience-lab/public/lib';checked=0
        for file in built.rglob('*'):
            if file.suffix!='.js' and not file.name.endswith('.d.ts'):continue
            shipped=public/file.relative_to(built)
            if not shipped.is_file() or file.read_bytes()!=shipped.read_bytes():raise SystemExit('Compiled artifact drift: '+str(shipped))
            checked+=1
        extras={p.relative_to(public).as_posix() for p in public.rglob('*.js')}-{p.relative_to(built).as_posix() for p in built.rglob('*.js')}
        if extras:raise SystemExit('Orphan compiled modules: '+str(sorted(extras)))
        print(f'Strict TypeScript and compiled artifact parity passed: {checked} JS/declaration files.')
if __name__=='__main__':main()
