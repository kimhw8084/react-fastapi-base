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
import tempfile
from typing import Protocol


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
    def __init__(self, root: Path, *, max_bytes: int = 100_000_000):
        if max_bytes < 1: raise ValueError('Storage limit must be positive.')
        self.root = root.resolve()
        self.max_bytes = max_bytes

    def _path(self, tenant_id: str, key: str) -> Path:
        tenant = _safe_segment(tenant_id, 'tenant identifier')
        relative = Path(tenant, *_safe_key(key).parts)
        path = (self.root / relative).resolve()
        if self.root not in path.parents: raise ValueError('Object path escaped storage root.')
        return path

    def put(self, tenant_id: str, key: str, content: bytes, content_type: str) -> StoredObject:
        if not isinstance(content, bytes) or len(content) > self.max_bytes: raise ValueError('Object exceeds the storage limit.')
        if not content_type or len(content_type) > 120 or any(char in content_type for char in ('\r', '\n')): raise ValueError('Invalid object content type.')
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


class MemoryStorage:
    def __init__(self): self._objects: dict[tuple[str, str], tuple[bytes, str]] = {}

    def put(self, tenant_id: str, key: str, content: bytes, content_type: str) -> StoredObject:
        _safe_segment(tenant_id, 'tenant identifier'); _safe_key(key)
        if not isinstance(content, bytes): raise ValueError('Objects must be bytes.')
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
