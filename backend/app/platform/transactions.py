from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.platform.database import Database

@contextmanager
def write_transaction(database: Database, tenant_id: str) -> Iterator[Session]:
    """Acquire the write reservation before reading mutable state.

    This coordinates only clients of the same qualified SQLite filesystem. It is
    not a distributed lock and cannot make an object-store mount safe.
    """
    with database.session(tenant_id) as session:
        try:
            session.execute(text('BEGIN IMMEDIATE'))
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
