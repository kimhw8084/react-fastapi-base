#!/usr/bin/env python3
"""Verify the actual widget layer, separately from React/PaaS release readiness."""
from datetime import datetime,timezone
import argparse,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['http','in_memory'],default='http');p.add_argument('--output',type=Path,default=ROOT/'evidence/current/lab');args=p.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'LAB_BROWSER_MODE':args.mode}
    checks=[]
    for name,command in [
      ('strict-types-and-artifact-parity',[sys.executable,'scripts/check_lab_build.py']),
      ('pure-model-tests',['node','--test','experience-lab/tests/model.test.mjs']),
      ('static-http-server',[sys.executable,'-m','pytest','-q','tests/test_lab_server.py']),
      ('catalog-drift',[sys.executable,'scripts/catalog.py','--check']),
      ('browser-interactions',[sys.executable,'-m','pytest','-q','experience-lab/tests/test_browser.py',f'--junitxml={output/"browser-junit.xml"}']),
    ]:
        print('RUN',name,flush=True)
        try:
            result=subprocess.run(command,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
            (output/f'{name}.log').write_text(result.stdout)
            checks.append({'name':name,'status':'PASS' if result.returncode==0 else 'FAIL','exit_code':result.returncode,'command':command,'log':f'{name}.log'})
        except (OSError,subprocess.TimeoutExpired) as e:checks.append({'name':name,'status':'BLOCKED','reason':str(e),'command':command})
        print(checks[-1]['status'],name,flush=True)
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'experience-lab').rglob('*') if p.is_file() and not set(p.parts)&{'__pycache__','.pytest_cache'}}
    report={'product':'react-fastapi-base','version':(ROOT/'VERSION').read_text(encoding='utf-8').strip(),'timestamp':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),'python_version':platform.python_version(),'node_version':subprocess.check_output(['node','--version'],text=True).strip(),'typescript_version':subprocess.check_output([str(ROOT/'frontend/node_modules/.bin/tsc') if (ROOT/'frontend/node_modules/.bin/tsc').is_file() else 'tsc','--version'],text=True).strip(),'browser_mode':args.mode,'checks':checks,'source_sha256':files,'lab_checks_pass':all(x['status']=='PASS' for x in checks),'react_host_verified':False,'macos_verified':False,'production_certified':False,'scope':'Compiled native widget layer. The in_memory mode does not test browser-to-HTTP serving or browser persistence. Neither mode certifies backend integration, full accessibility, manufacturing semantics or company infrastructure.'}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Report:',output/'verification.json')
    return 0 if report['lab_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
