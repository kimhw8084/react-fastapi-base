#!/usr/bin/env python3
"""Own disposable processes/data; never reuse a live application or database."""
from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
BACKEND_PYTHON=ROOT/'backend/.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')

def wait(url,process):
    for _ in range(100):
        if process.poll() is not None:raise RuntimeError('A disposable server exited before readiness.')
        try:
            with urllib.request.urlopen(url,timeout=1) as response:
                if response.status==200:return
        except OSError:pass
        time.sleep(.1)
    raise RuntimeError('Disposable server did not become ready.')

def main():
    if not (ROOT/'frontend/dist/index.html').is_file():raise RuntimeError('Build the actual frontend before browser tests.')
    if not BACKEND_PYTHON.is_file():raise RuntimeError('Create backend/.venv before running browser tests.')
    for port in (18081,4183):
        with socket.socket() as probe:probe.bind(('127.0.0.1',port))
    with tempfile.TemporaryDirectory(prefix='golden-e2e-') as temp:
        folder=Path(temp);data=folder/'data';runtime=folder/'runtime.json'
        runtime.write_text(json.dumps({'schemaVersion':1,'apiBase':'http://127.0.0.1:18081','defaultTheme':'operations','titleOverride':'Golden browser acceptance'}))
        env={k:v for k,v in os.environ.items() if not k.startswith('BASE_') and k not in ('AccessKey','NODE_ENV')}
        env.update(BASE_ENVIRONMENT='test',BASE_PROFILE='development',BASE_DEV_USER='demo.admin',BASE_DATA_ROOT=str(data),
            BASE_ALLOWED_ORIGINS='["http://127.0.0.1:4183"]',BASE_ALLOWED_HOSTS='["127.0.0.1","localhost"]',BASE_REQUEST_LIMIT_PER_MINUTE='1000',
            BASE_E2E_BASE='http://127.0.0.1:4183',BASE_FRONTEND_RUNTIME_CONFIG=str(runtime),PORT='4183',HOST='127.0.0.1')
        subprocess.check_call([str(BACKEND_PYTHON),'-m','app.cli','seed-demo'],cwd=ROOT/'backend',env=env)
        processes=[]
        try:
            processes.append(subprocess.Popen([str(BACKEND_PYTHON),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','18081'],cwd=ROOT/'backend',env=env))
            wait('http://127.0.0.1:18081/api/v1/readiness',processes[0])
            processes.append(subprocess.Popen(['node','server.mjs'],cwd=ROOT/'frontend',env=env))
            wait('http://127.0.0.1:4183/healthz',processes[1])
            return subprocess.call(['npm','run','test:e2e'],cwd=ROOT/'frontend',env=env)
        finally:
            for process in processes:
                if process.poll() is None:process.terminate()
            for process in processes:
                try:process.wait(timeout=8)
                except subprocess.TimeoutExpired:process.kill();process.wait()
if __name__=='__main__':raise SystemExit(main())
