from __future__ import annotations
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import RecordComment
from app.platform.schemas import CommentCreate, CommentRead
from app.platform.security import Actor
from app.platform.entity_registry import EntityRegistry

def list_comments(session: Session, actor: Actor, entity: str, entity_id: str, registry: EntityRegistry) -> list[CommentRead]:
    actor.require('read')
    registry.resolve(session, entity, entity_id)
    rows=session.scalars(select(RecordComment).where(RecordComment.entity==entity,RecordComment.entity_id==entity_id).order_by(RecordComment.created_at,RecordComment.id).limit(500)).all()
    return [CommentRead.model_validate(row) for row in rows]

def create_comment(session: Session, actor: Actor, entity: str, entity_id: str, data: CommentCreate, registry: EntityRegistry) -> CommentRead:
    actor.require('write')
    reference=registry.resolve(session,entity,entity_id)
    if reference.archived:
        raise AppError(409,'archived_readonly','Archived records are read-only, including comments.')
    row=RecordComment(id=str(uuid4()),workspace=reference.workspace,entity=entity,entity_id=entity_id,author=actor.user_id,body=data.body)
    session.add(row);session.flush()
    return CommentRead.model_validate(row)

def delete_comment(session: Session, actor: Actor, comment_id: str) -> None:
    actor.require('write')
    row=session.get(RecordComment,comment_id)
    if row is None: raise AppError(404,'comment_missing','Comment is not available.')
    if row.author!=actor.user_id and 'admin' not in actor.permissions: raise AppError(403,'comment_forbidden','Only the author or an administrator can remove this comment.')
    session.delete(row)
