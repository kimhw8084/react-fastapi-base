import hashlib
import json
from collections.abc import Callable
from typing import Any
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import IdempotencyEntry
from app.platform.security import Actor

def execute_once(session: Session, actor: Actor, key: str | None, operation: str,
                 payload: Any, action: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    if key is None:
        return action()
    if not 8 <= len(key) <= 128 or not all(c.isalnum() or c in '-_.' for c in key):
        raise AppError(400, 'invalid_idempotency_key', 'Use an 8–128 character idempotency key.')
    fingerprint = hashlib.sha256(json.dumps([operation,payload],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    existing = session.get(IdempotencyEntry,(actor.user_id,key))
    if existing:
        if existing.fingerprint != fingerprint:
            raise AppError(409,'idempotency_conflict','This operation key was already used for different input.')
        return existing.response
    response = action()
    session.add(IdempotencyEntry(owner=actor.user_id,key=key,fingerprint=fingerprint,response=response))
    return response
