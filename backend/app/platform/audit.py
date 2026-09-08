from typing import Any
from uuid import uuid4
from sqlalchemy.orm import Session
from app.platform.models import AuditEvent
from app.platform.security import Actor

def record_event(session: Session, actor: Actor, *, workspace: str, entity_id: str,
                 action: str, revision: int, before: dict[str, Any] | None,
                 after: dict[str, Any] | None) -> None:
    session.add(AuditEvent(id=str(uuid4()), actor=actor.user_id, workspace=workspace,
        entity_id=entity_id, action=action, revision=revision, before=before, after=after,
        request_id=actor.request_id))
