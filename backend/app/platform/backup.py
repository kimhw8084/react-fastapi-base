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

from app.platform.storage import LocalFilesystemStorage, StorageBackupAdapter, validate_object_key, validate_content_type


VERSION = 2


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


@contextmanager
def readonly(path: Path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('Source database is missing or a symbolic link.')
    connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        yield connection
    finally:
        connection.close()


def integrity(path: Path) -> None:
    with readonly(path) as connection:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite integrity check failed.')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Foreign key check failed.')


def _attachment_references(path: Path) -> list[dict[str, object]]:
    """Read object-backed attachment metadata without trusting its key."""
    with readonly(path) as connection:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='attachments'"
        ).fetchone()
        if table is None:
            return []
        rows = connection.execute(
            'SELECT object_key, size, sha256, content_type FROM attachments '
            'WHERE object_key IS NOT NULL ORDER BY object_key'
        ).fetchall()
    references: list[dict[str, object]] = []
    for object_key, size, digest, content_type in rows:
        if not isinstance(object_key, str):
            raise ValueError('Attachment object key is invalid.')
        try:
            validate_object_key(object_key)
        except ValueError as error:
            raise ValueError('Attachment object key is unsafe.') from error
        if isinstance(size, bool) or not isinstance(size, int) or size < 0 or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError('Attachment object metadata is invalid.')
        try:
            validate_content_type(content_type)
        except ValueError as error:
            raise ValueError('Attachment object metadata is invalid.') from error
        references.append({'object_key': object_key, 'size': size, 'sha256': digest, 'content_type': content_type})
    return references


def _safe_snapshot_source(snapshot_root: Path, value: str) -> Path:
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '\\' in value or ':' in value or not value:
        raise ValueError('Unsafe snapshot path.')
    source = snapshot_root / value
    if snapshot_root not in source.resolve(strict=False).parents:
        raise ValueError('Snapshot path escapes the snapshot root.')
    for parent in (source, *source.parents):
        if parent == snapshot_root:
            break
        if parent.is_symlink():
            raise ValueError('Snapshot contains a symbolic link.')
    return source


def _validate_database_path(value: str) -> None:
    path = PurePosixPath(value)
    if value == 'registry.sqlite3':
        return
    if len(path.parts) != 3 or path.parts[0] != 'tenants' or path.parts[2] != 'data.sqlite3':
        raise ValueError('Unknown snapshot database role.')
    try:
        canonical = str(UUID(path.parts[1]))
    except (ValueError, AttributeError, TypeError) as error:
        raise ValueError('Snapshot tenant database identifier is invalid.') from error
    if canonical != path.parts[1]:
        raise ValueError('Snapshot tenant database identifier is not canonical.')


def snapshot(
    root: Path,
    output: Path,
    *,
    maintenance: str,
    storage: StorageBackupAdapter | None = None,
) -> Path:
    """Publish an atomic database and object snapshot after full validation."""
    if maintenance != 'APP-STOPPED':
        raise ValueError('Stop all writers and acknowledge APP-STOPPED before a multi-database snapshot.')
    root = root.resolve()
    output = output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Backups must be outside the live data root.')
    if output.exists():
        raise ValueError('Snapshot target must not already exist.')
    adapter = storage or LocalFilesystemStorage(root / 'objects')
    if getattr(adapter, 'backup_mode', None) != 'application_snapshot':
        raise ValueError('The configured object provider has externally managed backup; obtain provider evidence before snapshotting.')

    registry = root / 'registry.sqlite3'
    paths = ['registry.sqlite3']
    with readonly(registry) as connection:
        tenants = connection.execute('SELECT id, active FROM tenants ORDER BY id').fetchall()
    omitted: list[str] = []
    for tenant_id, active in tenants:
        if str(UUID(tenant_id)) != tenant_id:
            raise ValueError('Invalid tenant registry entry.')
        relative = f'tenants/{tenant_id}/data.sqlite3'
        if not (root / relative).is_file() and not active:
            omitted.append(tenant_id)
            continue
        paths.append(relative)

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.golden-snapshot-', dir=output.parent))
    try:
        databases: list[dict[str, object]] = []
        references: dict[tuple[str, str], dict[str, object]] = {}
        for relative in paths:
            source = root / relative
            if root not in source.resolve(strict=False).parents:
                raise ValueError('Source path escaped the live root.')
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with readonly(source) as src:
                destination = sqlite3.connect(target)
                try:
                    src.backup(destination)
                finally:
                    destination.close()
            target.chmod(0o600)
            integrity(target)
            databases.append({'path': relative, 'size': target.stat().st_size, 'sha256': sha256(target)})
            if relative != 'registry.sqlite3':
                tenant_id = relative.split('/')[1]
                # Enumerate the database that will actually be published. The
                # live source remains untouched and cannot diverge from the
                # object manifest after the SQLite backup has completed.
                for reference in _attachment_references(target):
                    key = (tenant_id, str(reference['object_key']))
                    if key in references:
                        raise ValueError('Duplicate attachment object reference.')
                    references[key] = reference

        objects: list[dict[str, object]] = []
        for (tenant_id, object_key), reference in sorted(references.items()):
            snapshot_path = f'objects/{tenant_id}/{object_key}'
            stored = adapter.export_object(tenant_id, object_key, stage / snapshot_path, str(reference['content_type']))
            if stored.size != reference['size'] or stored.sha256 != reference['sha256']:
                raise ValueError('Referenced object does not match attachment metadata.')
            objects.append({
                'tenant_id': tenant_id,
                'object_key': object_key,
                'snapshot_path': snapshot_path,
                'size': stored.size,
                'sha256': stored.sha256,
                'content_type': str(reference['content_type']),
            })

        referenced = set(references)
        orphan_objects: list[dict[str, str]] = []
        if isinstance(adapter, LocalFilesystemStorage):
            for tenant_id, object_key in adapter.iter_object_keys():
                if (tenant_id, object_key) not in referenced:
                    orphan_objects.append({'tenant_id': tenant_id, 'object_key': object_key})

        manifest = {
            'schema_version': VERSION,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'consistency': 'application-wide snapshot requires APP-STOPPED and all trusted writers stopped',
            'databases': databases,
            'objects': objects,
            'orphan_objects': orphan_objects,
            'omitted_inactive_tenants': omitted,
        }
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        os.replace(stage, output)
        return output
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def restore(snapshot_root: Path, target_root: Path) -> Path:
    """Validate every database and object before atomically publishing a root."""
    snapshot_root = snapshot_root.resolve()
    target_root = target_root.absolute()
    if target_root.exists() or target_root.is_symlink():
        raise ValueError('Restore target must not exist; live overwrite is prohibited.')
    if snapshot_root == target_root or snapshot_root in target_root.parents:
        raise ValueError('Restore outside the snapshot directory.')
    try:
        manifest = json.loads((snapshot_root / 'manifest.json').read_text())
    except (OSError, ValueError, TypeError) as error:
        raise ValueError('Snapshot manifest is invalid.') from error
    if manifest.get('schema_version') != VERSION:
        raise ValueError('Unsupported snapshot version.')
    databases = manifest.get('databases')
    objects = manifest.get('objects')
    if not isinstance(databases, list) or not 1 <= len(databases) <= 1000 or not isinstance(objects, list) or len(objects) > 100_000:
        raise ValueError('Invalid snapshot resource lists.')

    database_entries: dict[str, dict[str, object]] = {}
    for entry in databases:
        if not isinstance(entry, dict) or not isinstance(entry.get('path'), str):
            raise ValueError('Invalid snapshot database entry.')
        value = entry['path']
        _validate_database_path(value)
        if value in database_entries or not isinstance(entry.get('size'), int) or not isinstance(entry.get('sha256'), str):
            raise ValueError('Invalid snapshot database metadata.')
        source = _safe_snapshot_source(snapshot_root, value)
        if not source.is_file() or source.stat().st_size != entry['size'] or sha256(source) != entry['sha256']:
            raise ValueError('Snapshot database checksum or size mismatch.')
        integrity(source)
        database_entries[value] = entry
    if 'registry.sqlite3' not in database_entries:
        raise ValueError('Snapshot is missing the registry.')

    object_entries: dict[tuple[str, str], dict[str, object]] = {}
    for entry in objects:
        if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) for key in ('tenant_id', 'object_key', 'snapshot_path', 'sha256', 'content_type')):
            raise ValueError('Invalid snapshot object entry.')
        tenant_id = entry['tenant_id']
        object_key = entry['object_key']
        try:
            if str(UUID(tenant_id)) != tenant_id:
                raise ValueError
            validate_object_key(object_key)
        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError('Snapshot object tenant or key is invalid.') from error
        if entry['snapshot_path'] != f'objects/{tenant_id}/{object_key}' or isinstance(entry.get('size'), bool) or not isinstance(entry.get('size'), int) or entry['size'] < 0 or len(entry['sha256']) != 64:
            raise ValueError('Snapshot object metadata is invalid.')
        try:
            validate_content_type(entry['content_type'])
        except ValueError as error:
            raise ValueError('Snapshot object metadata is invalid.') from error
        key = (tenant_id, object_key)
        if key in object_entries:
            raise ValueError('Duplicate snapshot object entry.')
        source = _safe_snapshot_source(snapshot_root, entry['snapshot_path'])
        if not source.is_file() or source.stat().st_size != entry['size'] or sha256(source) != entry['sha256']:
            raise ValueError('Snapshot object checksum or size mismatch.')
        object_entries[key] = entry

    with readonly(snapshot_root / 'registry.sqlite3') as connection:
        active_tenants = connection.execute('SELECT id FROM tenants WHERE active=1').fetchall()
    for tenant_id, in active_tenants:
        if f'tenants/{tenant_id}/data.sqlite3' not in database_entries:
            raise ValueError('Snapshot is missing an active tenant database.')

    for database_path in database_entries:
        if database_path == 'registry.sqlite3':
            continue
        tenant_id = database_path.split('/')[1]
        for reference in _attachment_references(snapshot_root / database_path):
            key = (tenant_id, str(reference['object_key']))
            entry = object_entries.get(key)
            if entry is None or entry['size'] != reference['size'] or entry['sha256'] != reference['sha256'] or entry['content_type'] != reference['content_type']:
                raise ValueError('Snapshot attachment metadata has no matching object.')

    target_root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.golden-restore-', dir=target_root.parent))
    try:
        for entry in database_entries.values():
            target = stage / str(entry['path'])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(snapshot_root / str(entry['path']), target)
            target.chmod(0o600)
            integrity(target)
        restored_storage = LocalFilesystemStorage(stage / 'objects')
        for entry in object_entries.values():
            restored = restored_storage.import_object(
                str(entry['tenant_id']), str(entry['object_key']), snapshot_root / str(entry['snapshot_path']), str(entry['content_type'])
            )
            if restored.size != entry['size'] or restored.sha256 != entry['sha256']:
                raise ValueError('Restored object checksum or size mismatch.')
        if target_root.exists():
            raise ValueError('Restore target appeared during restore; aborting.')
        os.rename(stage, target_root)
        return target_root
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
