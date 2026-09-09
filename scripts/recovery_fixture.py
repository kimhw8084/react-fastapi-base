#!/usr/bin/env python3
"""Run an actual disposable object-backed attachment backup/restore proof."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app.main import create_app  # noqa: E402
from app.platform.backup import restore, snapshot  # noqa: E402
from app.platform.database import Database  # noqa: E402
from app.platform.models import Attachment  # noqa: E402
from app.platform.provision import provision  # noqa: E402
from app.platform.settings import Settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/current/recovery/object-restore.json')
    args = parser.parse_args()
    started = datetime.now(timezone.utc)
    result: dict[str, object] = {
        'schema_version': 1,
        'source_commit': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip(),
        'timestamp': started.isoformat(),
        'command': [sys.executable, 'scripts/recovery_fixture.py', '--output', str(args.output)],
        'environment': {'platform': sys.platform, 'python': sys.version.split()[0]},
        'result': 'FAIL',
        'exit_code': 1,
    }
    try:
        with tempfile.TemporaryDirectory(prefix='react-fastapi-recovery-') as raw:
            temp = Path(raw)
            root = temp / 'live'
            settings = Settings(environment='test', profile='development', data_root=root, dev_user='alice')
            database = Database(settings)
            tenant_id = provision(database, 'Recovery fixture', 'alice')
            database.close()
            app = create_app(settings)
            body = b'rc2 object recovery fixture'
            with TestClient(app) as client:
                bootstrap = client.get('/api/v1/bootstrap')
                if bootstrap.status_code != 200:
                    raise RuntimeError('Fixture bootstrap failed.')
                client.headers.update({'X-Tenant-Id': tenant_id, 'X-CSRF-Token': bootstrap.json()['csrf_token']})
                record = client.post('/api/v1/work-items', json={'title': 'Recovery fixture record'})
                if record.status_code != 201:
                    raise RuntimeError('Fixture record creation failed.')
                record_id = record.json()['id']
                uploaded = client.post(
                    f'/api/v1/work-items/{record_id}/attachments',
                    json={'filename': 'recovery.txt', 'content_type': 'text/plain', 'content_base64': base64.b64encode(body).decode()},
                )
                if uploaded.status_code != 201:
                    raise RuntimeError('Fixture attachment upload failed.')
                attachment_id = uploaded.json()['id']
            metadata_database = Database(settings)
            with metadata_database.session(tenant_id) as session:
                object_key = session.get(Attachment, attachment_id).object_key
            metadata_database.close()
            if not object_key:
                raise RuntimeError('Fixture attachment was not object-backed.')
            source_object = root / 'objects' / tenant_id / object_key
            source_sha = hashlib.sha256(source_object.read_bytes()).hexdigest()
            backup = snapshot(root, temp / 'snapshot', maintenance='APP-STOPPED')
            snapshot_object = backup / json.loads((backup / 'manifest.json').read_text())['objects'][0]['snapshot_path']
            snapshot_sha = hashlib.sha256(snapshot_object.read_bytes()).hexdigest()
            restored_root = restore(backup, temp / 'restored')
            restored_settings = Settings(environment='test', profile='development', data_root=restored_root, dev_user='alice')
            restored_app = create_app(restored_settings)
            with TestClient(restored_app) as restored_client:
                bootstrap = restored_client.get('/api/v1/bootstrap')
                if bootstrap.status_code != 200:
                    raise RuntimeError('Restored fixture bootstrap failed.')
                restored_client.headers.update({'X-Tenant-Id': tenant_id, 'X-CSRF-Token': bootstrap.json()['csrf_token']})
                downloaded = restored_client.get(f'/api/v1/work-items/{record_id}/attachments/{attachment_id}')
                if downloaded.status_code != 200 or downloaded.content != body:
                    raise RuntimeError('Restored attachment download did not match the source bytes.')
                downloaded_sha = hashlib.sha256(downloaded.content).hexdigest()
            restored_object = restored_root / 'objects' / tenant_id / object_key
            restored_sha = hashlib.sha256(restored_object.read_bytes()).hexdigest()
            result.update({
                'tenant': tenant_id,
                'record_type': 'work_items',
                'record_id': record_id,
                'object_key': object_key,
                'source_object_sha': source_sha,
                'snapshot_object_sha': snapshot_sha,
                'restored_object_sha': restored_sha,
                'downloaded_object_sha': downloaded_sha,
                'result': 'PASS',
                'exit_code': 0,
            })
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return int(result['exit_code'])


if __name__ == '__main__':
    raise SystemExit(main())
