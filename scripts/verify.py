#!/usr/bin/env python3
"""Authoritative gate: missing tools/dependencies are BLOCKED, never SKIPPED/PASS."""
from __future__ import annotations
import argparse
import hashlib
import platform
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]

def verify(output: Path, source_only: bool=False, release: bool=False)->dict:
    output.mkdir(parents=True,exist_ok=True)
    results=[]
    def blocked(name,reason,required_for='code'):
        results.append({'name':name,'status':'BLOCKED','reason':reason,'required_for':required_for})
        print(f'BLOCKED {name}: {reason}',flush=True)
    def run(name,command,cwd=ROOT,timeout=300):
        print(f'RUN     {name}',flush=True)
        try:
            result=subprocess.run(command,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
            (output/(name+'.log')).write_text(result.stdout)
            row={'name':name,'status':'PASS' if result.returncode==0 else 'FAIL','exit_code':result.returncode,'log':name+'.log','command':command}
        except (OSError,subprocess.TimeoutExpired) as error:
            row={'name':name,'status':'BLOCKED','reason':str(error)}
        results.append(row);print(f"{row['status']:7} {name}",flush=True);return row['status']=='PASS'
    run('backend-tests',[sys.executable,'-m','pytest','-q',f'--junitxml={output.resolve()/"backend-junit.xml"}'],ROOT/'backend')
    run('tooling-tests',[sys.executable,'-m','pytest','-q','tests'],ROOT)
    run('architecture',[sys.executable,'scripts/check_architecture.py'])
    run('security-source',[sys.executable,'scripts/security_source_check.py'])
    run('version-metadata',[sys.executable,'scripts/version_check.py'])
    run('performance-owned-algorithms',[sys.executable,'scripts/performance_check.py'])
    run('performance-stress',[sys.executable,'scripts/performance_stress.py'])
    run('generated-contracts',[sys.executable,'scripts/generate_contracts.py','--check'])
    run('typescript-syntax-and-pure-client',['node','scripts/source_smoke.mjs'])
    run('static-server',['node','--test','frontend/tests/server.test.mjs'])
    run('localhost-http',[sys.executable,'scripts/http_smoke.py'])
    if source_only:
        blocked('engineering-widget-layer','Source-only request: native browser verification was not executed.')
    else:
        run('engineering-widget-layer',[sys.executable,'scripts/verify_lab.py','--mode',os.environ.get('LAB_BROWSER_MODE','http'),'--output',str((output/'native-lab').resolve())],timeout=600)
    run('required-catalog-completeness',[sys.executable,'scripts/catalog.py','--check','--release'])
    if source_only:
        blocked('upgrade-fixture','Source-only request: generated application upgrade proof was not executed.')
    elif release:
        run('upgrade-fixture',[sys.executable,'scripts/upgrade_fixture.py','--output',str((output/'upgrade-fixture.json').resolve())],timeout=600)
        run('reference-apps',[sys.executable,'scripts/reference_app_proof.py'],timeout=1200)
    else:
        blocked('upgrade-fixture','Release verification only; run `python3 dev verify-release` for the generated-app upgrade proof.','release')
    if source_only:
        blocked('macos-fresh-install','Source-only request; isolated clone execution was not run.','external')
    else:
        run('macos-fresh-install',[sys.executable,'scripts/fresh_clone_check.py','--output',str((output/'fresh-clone-macos.json').resolve())],timeout=1800)
    node_modules=ROOT/'frontend/node_modules'
    lock=ROOT/'frontend/package-lock.json'
    frontend=['frontend-typecheck','frontend-unit','frontend-build','frontend-storybook','browser-e2e-accessibility','npm-advisories']
    if source_only or not node_modules.is_dir() or not lock.is_file():
        reason='Source-only request.' if source_only else 'Dependency-resolved frontend installation and committed package-lock.json are required.'
        for name in frontend:blocked(name,reason)
    else:
        type_ok=run('frontend-typecheck',['npm','run','typecheck'],ROOT/'frontend')
        unit_ok=run('frontend-unit',['npm','test'],ROOT/'frontend')
        build_ok=run('frontend-build',['npm','run','build'],ROOT/'frontend')
        run('frontend-storybook',['npm','run','build:storybook'],ROOT/'frontend')
        if type_ok and unit_ok and build_ok:run('browser-e2e-accessibility',[sys.executable,'scripts/e2e_runner.py'],timeout=600)
        else:blocked('browser-e2e-accessibility','Frontend checks must pass first.')
        run('npm-advisories',['npm','audit','--audit-level=high'],ROOT/'frontend',120)
    if not source_only and importlib.util.find_spec('pip_audit'):
        run('python-advisories',[sys.executable,'-m','pip_audit','-r','backend/requirements.lock'],timeout=120)
    else:blocked('python-advisories','Install the audit tooling and enable network access; a version pin is not a vulnerability scan.')
    for name,reason in [
        ('company-identity','Two actual company users and the PaaS execution/ingress contract must be verified.'),
        ('company-storage','Provider-supported SQLite semantics, topology and durability are unverified. A probe cannot certify an S3 mount.'),
        ('company-deployment','Separate frontend/backend publishes and real browser routing have not been exercised here.'),
    ]:blocked(name,reason,'deployment')
    source_hashes={}
    for directory in ('backend','frontend','contracts','scripts','tests','experience-lab','catalog'):
        for file in sorted((ROOT/directory).rglob('*')):
            relative=file.relative_to(ROOT)
            if file.is_file() and not set(relative.parts)&{'__pycache__','.pytest_cache','.venv','venv','node_modules','dist','test-results','playwright-report'} and file.suffix not in {'.pyc','.log','.sqlite3'}:
                source_hashes[relative.as_posix()]=hashlib.sha256(file.read_bytes()).hexdigest()
    source_hashes['dev']=hashlib.sha256((ROOT/'dev').read_bytes()).hexdigest()
    source_digest=hashlib.sha256(json.dumps(source_hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (output/'source-hashes.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
    result={'schema_version':1,'source_digest':source_digest,'source_hashes':'source-hashes.json','python_version':platform.python_version(),'platform':platform.platform(),'created_at':datetime.now(timezone.utc).isoformat(),'timestamp':datetime.now(timezone.utc).isoformat(),'command':[sys.executable,'scripts/verify.py','--output',str(output),*(['--release'] if release else [])],'exit_code':0 if all(x['status']=='PASS' for x in results if x.get('required_for','code')=='code') else 1,'environment':{'platform':platform.platform(),'python':platform.python_version()},'hashes':{'source_digest':source_digest},'release_status':'NOT_CERTIFIED',
      'production_ready':False,'code_ready':all(x['status']=='PASS' for x in results if x.get('required_for','code')=='code'),'results':results,
      'note':'Company qualification is a separate operator-controlled release process. This tool never issues a production certificate from local test success.'}
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"NOT_CERTIFIED — report: {output/'verification.json'}")
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'.evidence/latest');p.add_argument('--source-only',action='store_true');p.add_argument('--release',action='store_true');a=p.parse_args()
    result=verify(a.output,a.source_only,a.release)
    # Code verification and deployment certification are separate. Exit zero proves only code gates.
    return 0 if result['code_ready'] else 1
if __name__=='__main__':raise SystemExit(main())
