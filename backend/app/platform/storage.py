"""Tenant-scoped object storage boundary.

The platform never assumes a company mount or a provider-specific filesystem.
Deployments inject an adapter; local development uses the safe filesystem
implementation and tests use the deterministic memory implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Iterator, Protocol


@dataclass(frozen=True)
class StoredObject:
    key: str
    size: int
    sha256: str
    content_type: str


class ObjectStorageAdapter(Protocol):
    def put(self, tenant_id: str, key: str, content: bytes, content_type: str) -> StoredObject: ...
    def get(self, tenant_id: str, key: str) -> bytes: ...
    def delete(self, tenant_id: str, key: str) -> None: ...
    def exists(self, tenant_id: str, key: str) -> bool: ...


class StorageBackupAdapter(Protocol):
    """Explicit boundary for object backup and restore.

    An object provider that owns retention and backup outside this application
    may advertise ``backup_mode = 'externally_managed'``.  The application
    snapshot must then record that fact rather than pretending a database-only
    snapshot contains the objects.
    """

    backup_mode: str

    def export_object(self, tenant_id: str, key: str, destination: Path, content_type: str) -> StoredObject: ...
    def import_object(self, tenant_id: str, key: str, source: Path, content_type: str) -> StoredObject: ...


def validate_content_type(content_type: str) -> str:
    """Validate the bounded metadata carried beside an object.

    MIME allowlisting belongs to the attachment service. Storage adapters still
    reject malformed metadata so an adapter cannot persist response-splitting
    characters or an unbounded content-type value.
    """
    if not isinstance(content_type, str) or not content_type or len(content_type) > 120 or any(char in content_type for char in ('\r', '\n')):
        raise ValueError('Invalid object content type.')
    return content_type


def validate_object_key(key: str) -> PurePosixPath:
    """Validate a provider-neutral object key using the storage path rules."""
    return _safe_key(key)


def _safe_segment(value: str, label: str) -> str:
    if not value or len(value) > 200 or value in {'.', '..'} or any(char in value for char in ('/', '\\', '\x00')):
        raise ValueError(f'Unsafe {label}.')
    return value


def _safe_key(key: str) -> PurePosixPath:
    path = PurePosixPath(key)
    if not key or path.is_absolute() or any(part in {'.', '..'} or '\\' in part or '\x00' in part for part in path.parts) or len(path.parts) > 12:
        raise ValueError('Unsafe object key.')
    for part in path.parts:
        _safe_segment(part, 'object key segment')
    return path


class LocalFilesystemStorage:
    backup_mode = 'application_snapshot'

    def __init__(self, root: Path, *, max_bytes: int = 100_000_000):
        if max_bytes < 1: raise ValueError('Storage limit must be positive.')
        self.root = root.resolve()
        self.max_bytes = max_bytes

    def _path(self, tenant_id: str, key: str) -> Path:
        tenant = _safe_segment(tenant_id, 'tenant identifier')
        relative = Path(tenant, *_safe_key(key).parts)
        path = self.root / relative
        resolved = path.resolve(strict=False)
        if resolved != self.root and self.root not in resolved.parents: raise ValueError('Object path escaped storage root.')
        if any(candidate.is_symlink() for candidate in (path, *path.parents) if candidate != self.root):
            raise ValueError('Symbolic links are not valid storage paths.')
        return path

    def put(self, tenant_id: str, key: str, content: bytes, content_type: str) -> StoredObject:
        if not isinstance(content, bytes) or len(content) > self.max_bytes: raise ValueError('Object exceeds the storage limit.')
        validate_content_type(content_type)
        target = self._path(tenant_id, key); target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.object-', dir=target.parent)
        try:
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(content); handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, target)
            target.chmod(0o600)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
        return StoredObject(key=key, size=len(content), sha256=hashlib.sha256(content).hexdigest(), content_type=content_type)

    def get(self, tenant_id: str, key: str) -> bytes:
        path = self._path(tenant_id, key)
        if path.is_symlink() or not path.is_file(): raise FileNotFoundError(key)
        return path.read_bytes()

    def delete(self, tenant_id: str, key: str) -> None:
        path = self._path(tenant_id, key)
        if path.is_symlink(): raise ValueError('Symbolic links are not valid objects.')
        if path.exists(): path.unlink()

    def exists(self, tenant_id: str, key: str) -> bool:
        path = self._path(tenant_id, key)
        return path.is_file() and not path.is_symlink()

    def export_object(self, tenant_id: str, key: str, destination: Path, content_type: str) -> StoredObject:
        validate_content_type(content_type)
        source = self._path(tenant_id, key)
        if source.is_symlink() or not source.is_file():
            raise FileNotFoundError(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            raise ValueError('Backup object destination already exists.')
        shutil.copyfile(source, destination)
        destination.chmod(0o600)
        content = destination.read_bytes()
        return StoredObject(key=key, size=len(content), sha256=hashlib.sha256(content).hexdigest(), content_type=content_type)

    def import_object(self, tenant_id: str, key: str, source: Path, content_type: str) -> StoredObject:
        validate_content_type(content_type)
        if source.is_symlink() or not source.is_file():
            raise ValueError('Snapshot object is missing or symbolic.')
        target = self._path(tenant_id, key)
        if target.exists() or target.is_symlink():
            raise ValueError('Restore object destination already exists.')
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f'.restore-{target.name}')
        try:
            shutil.copyfile(source, temporary)
            temporary.chmod(0o600)
            os.replace(temporary, target)
        finally:
            if temporary.exists() or temporary.is_symlink():
                temporary.unlink()
        content = target.read_bytes()
        return StoredObject(key=key, size=len(content), sha256=hashlib.sha256(content).hexdigest(), content_type=content_type)

    def iter_object_keys(self) -> Iterator[tuple[str, str]]:
        """Enumerate safe local objects for orphan reporting, never following links."""
        if not self.root.exists():
            return
        if self.root.is_symlink():
            raise ValueError('Object storage root must not be a symbolic link.')
        for path in sorted(self.root.rglob('*')):
            if path.is_symlink():
                raise ValueError('Symbolic links are not valid objects.')
            if not path.is_file():
                continue
            relative = path.relative_to(self.root)
            if len(relative.parts) < 2:
                raise ValueError('Object storage contains an invalid object path.')
            tenant_id = relative.parts[0]
            key = PurePosixPath(*relative.parts[1:]).as_posix()
            _safe_segment(tenant_id, 'tenant identifier')
            _safe_key(key)
            yield tenant_id, key


class MemoryStorage:
    def __init__(self): self._objects: dict[tuple[str, str], tuple[bytes, str]] = {}

    def put(self, tenant_id: str, key: str, content: bytes, content_type: str) -> StoredObject:
        _safe_segment(tenant_id, 'tenant identifier'); _safe_key(key)
        if not isinstance(content, bytes): raise ValueError('Objects must be bytes.')
        validate_content_type(content_type)
        self._objects[(tenant_id, key)] = (content, content_type)
        return StoredObject(key, len(content), hashlib.sha256(content).hexdigest(), content_type)

    def get(self, tenant_id: str, key: str) -> bytes:
        _safe_segment(tenant_id, 'tenant identifier'); _safe_key(key)
        try: return self._objects[(tenant_id, key)][0]
        except KeyError: raise FileNotFoundError(key) from None

    def delete(self, tenant_id: str, key: str) -> None:
        _safe_segment(tenant_id, 'tenant identifier'); _safe_key(key); self._objects.pop((tenant_id, key), None)

    def exists(self, tenant_id: str, key: str) -> bool:
        _safe_segment(tenant_id, 'tenant identifier'); _safe_key(key); return (tenant_id, key) in self._objects
