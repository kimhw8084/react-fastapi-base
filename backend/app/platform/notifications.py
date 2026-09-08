from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import Notification, NotificationPreference, utcnow
from app.platform.schemas import NotificationCreate, NotificationPreferenceRead, NotificationRead
from app.platform.security import Actor

def preference_enabled(session:Session,user_id:str,kind:str)->bool:
    row=session.get(NotificationPreference,(user_id,kind));return True if row is None else bool(row.enabled)

def create(session:Session,actor:Actor,data:NotificationCreate)->NotificationRead|None:
    actor.require('write')
    if not preference_enabled(session,data.user_id,data.kind):return None
    row=Notification(id=str(uuid4()),**data.model_dump())
    session.add(row);session.flush();return NotificationRead.model_validate(row)

def list_mine(session:Session,actor:Actor,*,unread_only:bool=False,limit:int=100)->list[NotificationRead]:
    query=select(Notification).where(Notification.user_id==actor.user_id,Notification.dismissed_at.is_(None)).order_by(Notification.created_at.desc()).limit(limit)
    if unread_only:query=query.where(Notification.read_at.is_(None))
    return [NotificationRead.model_validate(row) for row in session.scalars(query).all()]

def mark_read(session:Session,actor:Actor,notification_id:str)->NotificationRead:
    row=session.get(Notification,notification_id)
    if not row or row.user_id!=actor.user_id:raise AppError(404,'notification_missing','Notification is not available.')
    if row.read_at is None:row.read_at=datetime.now(timezone.utc);session.flush()
    return NotificationRead.model_validate(row)

def mark_all_read(session:Session,actor:Actor)->int:
    """Mark only the caller's visible notifications read; never cross a tenant/user boundary."""
    now=datetime.now(timezone.utc)
    rows=session.scalars(select(Notification).where(Notification.user_id==actor.user_id,Notification.dismissed_at.is_(None),Notification.read_at.is_(None))).all()
    for row in rows:row.read_at=now
    session.flush();return len(rows)

def dismiss(session:Session,actor:Actor,notification_id:str)->NotificationRead:
    row=session.get(Notification,notification_id)
    if not row or row.user_id!=actor.user_id:raise AppError(404,'notification_missing','Notification is not available.')
    row.dismissed_at=datetime.now(timezone.utc);row.read_at=row.read_at or row.dismissed_at;session.flush()
    return NotificationRead.model_validate(row)

def set_preference(session:Session,actor:Actor,kind:str,enabled:bool,revision:int|None)->NotificationPreferenceRead:
    if not kind or len(kind)>60 or any(not(c.isalnum() or c in '._-') for c in kind):raise AppError(422,'invalid_notification_kind','Notification kind is invalid.')
    row=session.get(NotificationPreference,(actor.user_id,kind))
    if row is None:
        if revision is not None:raise AppError(409,'revision_conflict','Notification preference does not exist yet.')
        row=NotificationPreference(user_id=actor.user_id,kind=kind,enabled=enabled,revision=1,updated_at=utcnow());session.add(row)
    else:
        if revision!=row.revision:raise AppError(409,'revision_conflict','Notification preference changed. Refresh and retry.',{'current_revision':row.revision})
        row.enabled=enabled;row.revision+=1;row.updated_at=utcnow()
    session.flush();return NotificationPreferenceRead.model_validate(row)
