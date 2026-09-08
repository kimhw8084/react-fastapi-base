from __future__ import annotations
import json
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import PlatformEvent, WebhookEndpoint
from app.platform import jobs
from app.platform.schemas import EventRead
from app.platform.security import Actor

def emit(session:Session,actor:Actor,topic:str,payload:dict,*,entity_type:str|None=None,entity_id:str|None=None)->EventRead:
    if not topic or len(topic)>100 or any(not(c.isalnum() or c in '._-') for c in topic):raise AppError(422,'invalid_event_topic','Event topic is invalid.')
    if len(json.dumps(payload,separators=(',',':'),default=str).encode())>64_000:raise AppError(413,'event_payload_too_large','Event payload is too large.')
    row=PlatformEvent(event_id=str(uuid4()),topic=topic,entity_type=entity_type,entity_id=entity_id,payload=payload,created_by=actor.user_id)
    session.add(row);session.flush()
    # Fan-out is durable: request transactions enqueue delivery work but never wait
    # on external networks. Endpoint URL/secret validation happens again in worker.
    for endpoint in session.scalars(select(WebhookEndpoint).where(WebhookEndpoint.enabled.is_(True))).all():
        if topic in (endpoint.topics or []):
            jobs.enqueue(session,actor,'webhook.deliver',{'endpoint_id':endpoint.id,'event_id':row.event_id},max_attempts=5)
    return EventRead.model_validate(row)

def list_events(session:Session,actor:Actor,*,after:int=0,topics:list[str]|None=None,limit:int=100)->list[EventRead]:
    actor.require('read');query=select(PlatformEvent).where(PlatformEvent.sequence>after).order_by(PlatformEvent.sequence).limit(limit)
    if topics:query=query.where(PlatformEvent.topic.in_(topics))
    return [EventRead.model_validate(row) for row in session.scalars(query).all()]
