#!/usr/bin/env python3
"""Run the source-bound two-process independent deployment qualification."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
FRONTEND = ROOT / 'frontend'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

from app.platform.deployment_contract import (  # noqa: E402
    contract_sha256,
    load_contract,
    validate_independent_runtime_config,
    validate_public_deployment_descriptor,
)
from app.platform.version import API_CONTRACT_REVISION, API_MAJOR  # noqa: E402
from scripts.release_version import read_candidate_version  # noqa: E402
from scripts.source_manifest import source_provenance  # noqa: E402


CHECKS = (
    'provision_disposable_data',
    'frontend_build',
    'frontend_static_health',
    'frontend_static_content',
    'frontend_api_not_proxied',
    'backend_health',
    'backend_readiness',
    'cors_allows_configured_origin',
    'cors_rejects_unconfigured_origin',
    'runtime_config_public_schema',
    'cross_origin_api_bootstrap',
    'api_compatibility_current_pair',
    'api_compatibility_incompatible_major',
    'api_compatibility_older_revision',
    'runtime_origin_rejections',
    'production_descriptor_rejections',
    'frontend_stop_does_not_proxy_backend',
    'backend_stop_does_not_serve_frontend',
    'browser_api_bootstrap',
)


class QualificationFailure(RuntimeError):
    pass


def _available(port: int) -> bool:
    with socket.socket() as listener:
        try:
            listener.bind(('127.0.0.1', port))
        except OSError:
            return False
    return True


def _environment() -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if not key.startswith('BASE_') and key != 'AccessKey'}
    environment.pop('PORT', None)
    environment.pop('HOST', None)
    environment.pop('NODE_ENV', None)
    return environment


def _run(command: list[str], *, cwd: Path, environment: dict[str, str], timeout: int = 180) -> bool:
    try:
        result = subprocess.run(command, cwd=cwd, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _stop(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=8)


def _wait_for(url: str, *, process: subprocess.Popen[str], headers: dict[str, str] | None = None, expected: int = 200) -> bool:
    for _ in range(120):
        if process.poll() is not None:
            return False
        try:
            response = httpx.get(url, headers=headers, timeout=1.5, trust_env=False)
            if response.status_code == expected:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    return False


def _browser_bootstrap(frontend_origin: str) -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                response = page.goto(frontend_origin, wait_until='domcontentloaded', timeout=15000)
                if response is None or response.status != 200:
                    return False
                page.locator('.brand').wait_for(state='visible', timeout=15000)
                return 'Workspace unavailable' not in page.locator('body').inner_text()
            finally:
                browser.close()
    except Exception:
        return False


def qualify(output: Path, *, backend_port: int = 18000, frontend_port: int = 14173) -> dict[str, Any]:
    contract = load_contract()
    provenance = source_provenance(ROOT)
    version = read_candidate_version(ROOT).version
    backend_origin = f'http://127.0.0.1:{backend_port}'
    frontend_origin = f'http://127.0.0.1:{frontend_port}'
    checks: dict[str, dict[str, str]] = {name: {'status': 'FAIL'} for name in CHECKS}
    failures: list[str] = []
    backend_process: subprocess.Popen[str] | None = None
    frontend_process: subprocess.Popen[str] | None = None

    def check(name: str, action: Callable[[], bool]) -> bool:
        try:
            passed = bool(action())
        except Exception:
            passed = False
        checks[name] = {'status': 'PASS' if passed else 'FAIL'}
        if not passed:
            failures.append(name)
        return passed

    def require(name: str, action: Callable[[], bool]) -> None:
        if not check(name, action):
            raise QualificationFailure(name)

    try:
        if not _available(backend_port) or not _available(frontend_port):
            raise QualificationFailure('distinct_loopback_ports')
        with tempfile.TemporaryDirectory(prefix='independent-deployment-proof-') as raw:
            temporary = Path(raw)
            data_root = temporary / 'data'
            runtime_path = temporary / 'runtime-config.json'
            environment = _environment()
            environment.update({
                'BASE_ENVIRONMENT': 'test',
                'BASE_PROFILE': 'development',
                'BASE_DEV_USER': 'demo.admin',
                'BASE_DATA_ROOT': str(data_root),
                'BASE_ALLOWED_ORIGINS': json.dumps([frontend_origin]),
                'BASE_ALLOWED_HOSTS': json.dumps(['127.0.0.1']),
                'BASE_ATTACHMENT_UPLOAD_MODE': 'disabled',
            })
            runtime_config = {'schemaVersion': 1, 'apiBase': backend_origin, 'defaultTheme': 'operations', 'titleOverride': ''}
            runtime_path.write_text(json.dumps(runtime_config), encoding='utf-8')
            require('provision_disposable_data', lambda: _run([sys.executable, '-m', 'app.cli', 'provision', '--tenant', 'Independent deployment qualification', '--admin', 'demo.admin'], cwd=BACKEND, environment=environment))
            require('frontend_build', lambda: _run(['npm', 'run', 'build'], cwd=FRONTEND, environment=environment, timeout=300))

            backend_environment = {**environment, 'PORT': str(backend_port), 'HOST': '127.0.0.1'}
            backend_process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(backend_port)], cwd=BACKEND, env=backend_environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            require('backend_health', lambda: _wait_for(backend_origin + '/api/v1/health', process=backend_process))
            require('backend_readiness', lambda: _wait_for(backend_origin + '/api/v1/readiness', process=backend_process))

            frontend_environment = _environment()
            frontend_environment.update({'NODE_ENV': 'test', 'PORT': str(frontend_port), 'HOST': '127.0.0.1', 'BASE_FRONTEND_HOSTS': json.dumps(['127.0.0.1']), 'BASE_FRONTEND_RUNTIME_CONFIG': str(runtime_path)})
            frontend_process = subprocess.Popen(['node', 'server.mjs'], cwd=FRONTEND, env=frontend_environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            require('frontend_static_health', lambda: _wait_for(frontend_origin + '/healthz', process=frontend_process))

            with httpx.Client(timeout=10, trust_env=False) as client:
                static = client.get(frontend_origin + '/', headers={'Host': f'127.0.0.1:{frontend_port}', 'Accept': 'text/html'})
                check('frontend_static_content', lambda: static.status_code == 200 and '<div id="root"></div>' in static.text)
                api_fallback = client.get(frontend_origin + '/api/v1/bootstrap', headers={'Accept': 'text/html'})
                check('frontend_api_not_proxied', lambda: api_fallback.status_code == 404 and 'API is published separately' in api_fallback.text)
                runtime_response = client.get(frontend_origin + '/runtime-config.json')
                check('runtime_config_public_schema', lambda: runtime_response.status_code == 200 and validate_independent_runtime_config(runtime_response.json(), frontend_origin=frontend_origin, backend_origin=backend_origin) == runtime_config)

                allowed = client.options(backend_origin + '/api/v1/bootstrap', headers={'Origin': frontend_origin, 'Access-Control-Request-Method': 'GET'})
                check('cors_allows_configured_origin', lambda: allowed.status_code == 200 and allowed.headers.get('access-control-allow-origin') == frontend_origin)
                rejected = client.options(backend_origin + '/api/v1/bootstrap', headers={'Origin': 'http://127.0.0.1:14174', 'Access-Control-Request-Method': 'GET'})
                check('cors_rejects_unconfigured_origin', lambda: rejected.status_code >= 400 and rejected.headers.get('access-control-allow-origin') != 'http://127.0.0.1:14174')
                bootstrap = client.get(backend_origin + '/api/v1/bootstrap', headers={'Origin': frontend_origin})
                payload = bootstrap.json() if bootstrap.headers.get('content-type', '').startswith('application/json') else {}
                check('backend_health', lambda: bootstrap.status_code == 200 and payload.get('user_id') == 'demo.admin')
                check('cross_origin_api_bootstrap', lambda: bootstrap.status_code == 200 and bootstrap.headers.get('access-control-allow-origin') == frontend_origin and payload.get('api_major') == API_MAJOR and payload.get('api_revision') == API_CONTRACT_REVISION)

                compatibility = contract['api_compatibility']
                accepts = lambda major, revision: major == compatibility['major'] and revision >= compatibility['frontend_compiled_revision']
                check('api_compatibility_current_pair', lambda: accepts(payload.get('api_major'), payload.get('api_revision')))
                check('api_compatibility_incompatible_major', lambda: not accepts(compatibility['major'] + 1, compatibility['frontend_compiled_revision']))
                check('api_compatibility_older_revision', lambda: not accepts(compatibility['major'], compatibility['frontend_compiled_revision'] - 1))

            def runtime_rejections() -> bool:
                candidates = [
                    {'schemaVersion': 1, 'apiBase': '', 'defaultTheme': 'operations', 'titleOverride': ''},
                    {'schemaVersion': 1, 'apiBase': backend_origin + '/api/v1', 'defaultTheme': 'operations', 'titleOverride': ''},
                    {'schemaVersion': 1, 'apiBase': 'https://user:password@example.test', 'defaultTheme': 'operations', 'titleOverride': ''},
                    {'schemaVersion': 1, 'apiBase': 'http://backend.example.test', 'defaultTheme': 'operations', 'titleOverride': ''},
                ]
                return all(_rejects(candidate, frontend_origin=frontend_origin, backend_origin=backend_origin) for candidate in candidates) and _rejects(
                    runtime_config, frontend_origin='https://frontend.example.test', backend_origin='http://backend.example.test', production=True,
                )

            def _rejects(value: dict[str, Any], **kwargs: Any) -> bool:
                try:
                    validate_independent_runtime_config(value, **kwargs)
                except ValueError:
                    return True
                return False

            def _production_rejections() -> bool:
                for kwargs in (
                    {'frontend_origin': 'http://frontend.example.test', 'backend_origin': 'https://backend.example.test', 'frontend_hosts': ['frontend.example.test'], 'backend_hosts': ['backend.example.test'], 'production': True},
                    {'frontend_origin': 'https://localhost', 'backend_origin': 'https://backend.example.test', 'frontend_hosts': ['localhost'], 'backend_hosts': ['backend.example.test'], 'production': True},
                ):
                    try:
                        validate_public_deployment_descriptor(**kwargs)
                    except ValueError:
                        continue
                    return False
                return True

            check('runtime_origin_rejections', runtime_rejections)
            check('production_descriptor_rejections', _production_rejections)

            check('browser_api_bootstrap', lambda: _browser_bootstrap(frontend_origin))

            _stop(frontend_process)
            check('frontend_stop_does_not_proxy_backend', lambda: _backend_remains_and_frontend_is_down(backend_origin, frontend_origin, backend_process))
            frontend_process = subprocess.Popen(['node', 'server.mjs'], cwd=FRONTEND, env=frontend_environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            require('frontend_static_health', lambda: _wait_for(frontend_origin + '/healthz', process=frontend_process))
            _stop(backend_process)
            check('backend_stop_does_not_serve_frontend', lambda: _frontend_remains_and_backend_is_down(frontend_origin, backend_origin, frontend_process))
    except QualificationFailure as failure:
        if str(failure) not in failures:
            failures.append(str(failure))
    finally:
        _stop(frontend_process)
        _stop(backend_process)

    evidence = {
        'schema_version': 1,
        'report_type': 'repository-independent-deployment-qualification',
        'status': 'PASS' if not failures and all(row['status'] == 'PASS' for row in checks.values()) else 'FAIL',
        'repository_deployment_status': 'PASS' if not failures and all(row['status'] == 'PASS' for row in checks.values()) else 'FAIL',
        'company_deployment_status': 'BLOCKED_EXTERNAL',
        'company_qualification': 'BLOCKED_EXTERNAL',
        'production_ready': False,
        'qualification_environment': 'test',
        'qualification_profile': 'development',
        'candidate_version': version,
        'candidate_head': provenance['executable_source_commit'],
        'executable_source_commit': provenance['executable_source_commit'],
        'source_digest': provenance['source_digest'],
        'contract_sha256': contract_sha256(),
        'frontend_api_base': backend_origin,
        'process_roles': {
            'frontend': {'role': 'frontend_static_node_publisher', 'origin': frontend_origin, 'host': '127.0.0.1', 'port': frontend_port},
            'backend': {'role': 'backend_asgi_service', 'origin': backend_origin, 'host': '127.0.0.1', 'port': backend_port},
        },
        'checks': checks,
        'failure_checks': sorted(set(failures)),
        'note': 'Repository proof covers independently published software units only; company publication, ingress, session, restart, redeploy and recovery qualification remain external.',
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return evidence


def _backend_remains_and_frontend_is_down(backend_origin: str, frontend_origin: str, backend_process: subprocess.Popen[str]) -> bool:
    try:
        backend_ok = httpx.get(backend_origin + '/api/v1/health', timeout=3, trust_env=False).status_code == 200
    except httpx.HTTPError:
        backend_ok = False
    try:
        frontend_down = False
        httpx.get(frontend_origin + '/healthz', timeout=1, trust_env=False)
    except httpx.HTTPError:
        frontend_down = True
    try:
        backend_root = httpx.get(backend_origin + '/', timeout=3, trust_env=False)
        backend_static = backend_root.status_code == 200
    except httpx.HTTPError:
        backend_static = True
    return backend_ok and frontend_down and not backend_static and backend_process.poll() is None


def _frontend_remains_and_backend_is_down(frontend_origin: str, backend_origin: str, frontend_process: subprocess.Popen[str]) -> bool:
    try:
        frontend_ok = httpx.get(frontend_origin + '/healthz', timeout=3, trust_env=False).status_code == 200
        frontend_api = httpx.get(frontend_origin + '/api/v1/health', timeout=3, trust_env=False).status_code == 404
    except httpx.HTTPError:
        frontend_ok = False
        frontend_api = False
    try:
        httpx.get(backend_origin + '/api/v1/health', timeout=1, trust_env=False)
        backend_down = False
    except httpx.HTTPError:
        backend_down = True
    return frontend_ok and frontend_api and backend_down and frontend_process.poll() is None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/deployment/qualification.json')
    parser.add_argument('--backend-port', type=int, default=18000)
    parser.add_argument('--frontend-port', type=int, default=14173)
    args = parser.parse_args()
    try:
        evidence = qualify(args.output.resolve(), backend_port=args.backend_port, frontend_port=args.frontend_port)
    except Exception:
        print('Independent deployment qualification FAILED: evidence could not be produced.')
        return 1
    if evidence['status'] != 'PASS':
        print('Independent deployment qualification FAILED: one or more repository checks failed.')
        return 1
    print(f"Independent deployment qualification PASS: {args.output}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
