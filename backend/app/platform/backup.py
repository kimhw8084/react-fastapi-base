from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
from uuid import UUID

VERSION=1

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

@contextmanager
def readonly(path: Path):
    if path.is_symlink() or not path.is_file():raise ValueError('Source database is missing or a symbolic link.')
    connection=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    try:
        yield connection
    finally:
        connection.close()

def integrity(path: Path) -> None:
    with readonly(path) as connection:
        if connection.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity check failed.')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:raise ValueError('Foreign key check failed.')

def snapshot(root: Path, output: Path, *, maintenance: str) -> Path:
    if maintenance!='APP-STOPPED':raise ValueError('Stop all writers and acknowledge APP-STOPPED before a multi-database snapshot.')
    root=root.resolve();output=output.resolve()
    if output==root or root in output.parents:raise ValueError('Backups must be outside the live data root.')
    if output.exists():raise ValueError('Snapshot target must not already exist.')
    paths=['registry.sqlite3']
    with readonly(root/'registry.sqlite3') as connection:
        tenants=connection.execute('SELECT id, active FROM tenants ORDER BY id').fetchall()
    omitted=[]
    for tenant_id,active in tenants:
        if str(UUID(tenant_id))!=tenant_id:raise ValueError('Invalid tenant registry entry.')
        relative=f'tenants/{tenant_id}/data.sqlite3'
        if not (root/relative).is_file() and not active:omitted.append(tenant_id);continue
        paths.append(relative)
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.golden-snapshot-',dir=output.parent))
    try:
        files=[]
        for relative in paths:
            source=root/relative
            if root not in source.resolve().parents:raise ValueError('Source path escaped the live root.')
            target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True)
            with readonly(source) as src:
                dst=sqlite3.connect(target)
                try:
                    src.backup(dst)
                finally:
                    dst.close()
            target.chmod(0o600);integrity(target)
            files.append({'path':relative,'size':target.stat().st_size,'sha256':sha256(target)})
        manifest={'schema_version':VERSION,'created_at':datetime.now(timezone.utc).isoformat(),
                  'consistency':'per-database SQLite backup; application-wide consistency requires external quiescence',
                  'files':files,'omitted_inactive_tenants':omitted}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2))
        os.replace(stage,output)
        return output
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True)
        raise

def restore(snapshot_root: Path,target_root: Path) -> Path:
    snapshot_root=snapshot_root.resolve();target_root=target_root.absolute()
    if target_root.exists() or target_root.is_symlink():raise ValueError('Restore target must not exist; live overwrite is prohibited.')
    if snapshot_root==target_root or snapshot_root in target_root.parents:raise ValueError('Restore outside the snapshot directory.')
    manifest=json.loads((snapshot_root/'manifest.json').read_text())
    if manifest.get('schema_version')!=VERSION:raise ValueError('Unsupported snapshot version.')
    entries=manifest.get('files')
    if not isinstance(entries,list) or not 1<=len(entries)<=1000:raise ValueError('Invalid snapshot file list.')
    seen=set()
    for entry in entries:
        value=entry['path'];path=PurePosixPath(value)
        if path.is_absolute() or '..' in path.parts or '\\' in value or ':' in value or value in seen:raise ValueError('Unsafe snapshot path.')
        if value!='registry.sqlite3':
            if len(path.parts)!=3 or path.parts[0]!='tenants' or path.parts[2]!='data.sqlite3' or str(UUID(path.parts[1]))!=path.parts[1]:
                raise ValueError('Unknown snapshot file role.')
        source=snapshot_root/value
        if source.is_symlink() or snapshot_root not in source.resolve().parents:raise ValueError('Snapshot contains a symbolic link or escaping path.')
        if not source.is_file() or source.stat().st_size!=entry['size'] or sha256(source)!=entry['sha256']:raise ValueError('Snapshot checksum or size mismatch.')
        integrity(source);seen.add(value)
    if 'registry.sqlite3' not in seen:raise ValueError('Snapshot is missing the registry.')
    with readonly(snapshot_root/'registry.sqlite3') as connection:
        for tenant_id, in connection.execute('SELECT id FROM tenants WHERE active=1'):
            if f'tenants/{tenant_id}/data.sqlite3' not in seen:raise ValueError('Snapshot is missing an active tenant database.')
    target_root.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.golden-restore-',dir=target_root.parent))
    try:
        for entry in entries:
            target=stage/entry['path'];target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(snapshot_root/entry['path'],target);target.chmod(0o600)
        if target_root.exists():raise ValueError('Restore target appeared during restore; aborting.')
        os.rename(stage,target_root)
        return target_root
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True)
        raise
