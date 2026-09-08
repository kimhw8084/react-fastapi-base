from __future__ import annotations
from pathlib import Path
from threading import RLock
from uuid import UUID
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from app.platform.errors import AppError
from app.platform.settings import Settings

class Database:
    """One connection policy for API and trusted local tooling. No request-time DDL."""
    def __init__(self, settings: Settings):
        self.settings = settings
        self.root = settings.data_root.resolve()
        self._engines: dict[str, Engine] = {}
        self._lock = RLock()

    def path(self, tenant_id: str | None = None) -> Path:
        target = self.root / 'registry.sqlite3'
        if tenant_id is not None:
            try:
                canonical = str(UUID(tenant_id))
            except (ValueError, TypeError, AttributeError):
                raise AppError(400, 'invalid_tenant', 'Tenant identifier is invalid.') from None
            if canonical != tenant_id:
                raise AppError(400, 'invalid_tenant', 'Tenant identifier must be canonical.')
            target = self.root / 'tenants' / canonical / 'data.sqlite3'
        if self.root not in target.resolve().parents or any(p.is_symlink() for p in [target, *target.parents] if p != Path('/')):
            raise AppError(503, 'unsafe_storage_path', 'Database path is not an approved local path.')
        return target

    def engine(self, tenant_id: str | None = None, *, provision: bool = False) -> Engine:
        path = self.path(tenant_id)
        if not provision and not path.is_file():
            raise AppError(503, 'database_unavailable', 'Database is not provisioned. Run operator migrations.')
        if provision:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self._lock:
            key = str(path)
            if key not in self._engines:
                if len(self._engines) >= 64:
                    self._engines.pop(next(iter(self._engines))).dispose()
                # rw prevents an accidentally deleted database being silently recreated.
                url = f'sqlite:///file:{path}?mode={"rwc" if provision else "rw"}&uri=true'
                engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': self.settings.busy_timeout_ms / 1000}, poolclass=NullPool)
                @event.listens_for(engine, 'connect')
                def configure(connection, _):
                    connection.execute('PRAGMA foreign_keys=ON')
                    connection.execute(f'PRAGMA busy_timeout={self.settings.busy_timeout_ms}')
                    connection.execute('PRAGMA synchronous=FULL')
                    # Never switch a live database's journal mode from a request.
                    mode = connection.execute('PRAGMA journal_mode').fetchone()[0].lower()
                    if mode != 'delete':
                        raise RuntimeError('This release supports DELETE journalling only on qualified storage.')
                self._engines[key] = engine
            return self._engines[key]

    def session(self, tenant_id: str | None = None) -> Session:
        return Session(self.engine(tenant_id), expire_on_commit=False)

    def close(self) -> None:
        for engine in self._engines.values():
            engine.dispose()
        self._engines.clear()
