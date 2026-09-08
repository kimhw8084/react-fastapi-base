#!/usr/bin/env python3
"""Real localhost Uvicorn + HTTP acceptance. Owns and removes disposable data only."""
from __future__ import annotations
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from uuid import uuid4
import httpx
ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name);print('PASS '+name,flush=True)
    with tempfile.TemporaryDirectory(prefix='golden-http-proof-') as temp:
        folder=Path(temp)
        env={k:v for k,v in os.environ.items() if not k.startswith('BASE_') and k!='AccessKey'}
        env.update(BASE_ENVIRONMENT='test',BASE_PROFILE='development',BASE_DEV_USER='demo.admin',BASE_DATA_ROOT=str(folder/'data'))
        subprocess.run([sys.executable,'-m','app.cli','seed-demo'],cwd=ROOT/'backend',env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        log=(folder/'server.log').open('w')
        process=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT/'backend',env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=10,trust_env=False) as client:
                for _ in range(100):
                    if process.poll() is not None:raise RuntimeError('Server exited: '+(folder/'server.log').read_text())
                    try:
                        if client.get('/api/v1/readiness').status_code==200:break
                    except httpx.TransportError:pass
                    time.sleep(.1)
                else:raise RuntimeError('Server did not become ready.')
                check('readiness',client.get('/api/v1/readiness').json()['ready'])
                boot=client.get('/api/v1/bootstrap').json()
                check('explicit-development-identity',boot['user_id']=='demo.admin')
                client.headers['X-Tenant-Id']=boot['tenants'][0]['id']
                check('missing-CSRF-rejected',client.post('/api/v1/work-items',json={'title':'Rejected'}).status_code==403)
                client.headers['X-CSRF-Token']=boot['csrf_token']
                key=str(uuid4());payload={'title':'Real HTTP acceptance','description':'Disposable proof'}
                created=client.post('/api/v1/work-items',json=payload,headers={'Idempotency-Key':key})
                check('create',created.status_code==201)
                item=created.json();url='/api/v1/work-items/'+item['id']
                check('idempotent-replay',client.post('/api/v1/work-items',json=payload,headers={'Idempotency-Key':key}).json()['id']==item['id'])
                check('request-correlation',bool(created.headers.get('x-request-id')))
                changed=client.put(url,json={**payload,'title':'Changed once','revision':item['revision']})
                check('revision-update',changed.status_code==200 and changed.json()['revision']==2)
                check('stale-write-rejected',client.put(url,json={**payload,'revision':1}).status_code==409)
                check('untrusted-user-header-ignored',client.get('/api/v1/identity-proof',headers={'X-User-Id':'some.other.user'}).json()['user_id']=='demo.admin')
                check('foreign-tenant-denied',client.get('/api/v1/work-items',headers={'X-Tenant-Id':str(uuid4())}).status_code==403)
                check('history',len(client.get(url+'/history').json())==2)
                view=client.post('/api/v1/workspaces/work_items/views',json={'name':'HTTP proof','definition':{'search':'Changed'}})
                check('saved-view-create',view.status_code==201)
                check('saved-view-exact-link',client.get('/api/v1/workspaces/work_items/views/'+view.json()['id']).json()['name']=='HTTP proof')
                archive=client.post(url+'/lifecycle/archive',json={'revision':2})
                check('archive',archive.status_code==200 and archive.json()['archived'])
                check('archived-read-only',client.put(url,json={**payload,'revision':3}).status_code==409)
                check('restore',client.post(url+'/lifecycle/restore',json={'revision':3}).status_code==200)
                csv=client.get('/api/v1/work-items/export.csv')
                check('schema-versioned-export',csv.status_code==200 and csv.text.startswith('# golden-work-items/1'))
                preview=client.post('/api/v1/work-items/import/preview',json={'csv':csv.text})
                check('export-import-preview',preview.status_code==200 and not preview.json()['errors'])
                check('error-envelope',client.get('/api/v1/does-not-exist').json()['error']['code']=='http_error')
        finally:
            if process.poll() is None:process.terminate()
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            log.close()
        print(json.dumps({'scope':'localhost-real-HTTP-only','checks_passed':len(checks),'company_certified':False}))
    return 0
if __name__=='__main__':raise SystemExit(main())
