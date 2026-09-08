from __future__ import annotations
import hashlib
import hmac
import json
import os
from urllib.parse import urlsplit
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import WebhookDelivery, WebhookEndpoint, utcnow
from app.platform.schemas import WebhookDeliveryRead, WebhookEndpointRead, WebhookEndpointWrite
from app.platform.security import Actor
from app.platform.settings import Settings

def validate_url(url:str,settings:Settings)->str:
    parsed=urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise AppError(422,'unsafe_webhook_url','Outbound webhooks require an exact HTTPS URL without credentials or fragments.')
    host=parsed.hostname.lower().rstrip('.')
    if host not in settings.webhook_allowed_hosts:
        raise AppError(422,'webhook_host_not_allowed','Webhook host is not in the deployment allowlist.')
    if parsed.port not in (None,443):raise AppError(422,'unsafe_webhook_url','Webhook URL may only use the default HTTPS port.')
    return url

def secret_for(ref:str)->str:
    value=os.environ.get('BASE_WEBHOOK_SECRET_'+ref,'')
    if len(value)<32:raise AppError(503,'webhook_secret_unavailable','Webhook signing secret is unavailable or too short.')
    return value

def sign(secret:str,timestamp:int,body:bytes)->str:
    return hmac.new(secret.encode(),str(timestamp).encode()+b'.'+body,hashlib.sha256).hexdigest()

def list_endpoints(session:Session,actor:Actor)->list[WebhookEndpointRead]:
    actor.require('admin');return [WebhookEndpointRead.model_validate(row) for row in session.scalars(select(WebhookEndpoint).order_by(WebhookEndpoint.name)).all()]

def list_deliveries(session:Session,actor:Actor,endpoint_id:str,limit:int=100)->list[WebhookDeliveryRead]:
    actor.require('admin')
    if session.get(WebhookEndpoint,endpoint_id) is None:raise AppError(404,'webhook_missing','Webhook endpoint is not available.')
    rows=session.scalars(select(WebhookDelivery).where(WebhookDelivery.endpoint_id==endpoint_id).order_by(WebhookDelivery.created_at.desc()).limit(limit)).all()
    return [WebhookDeliveryRead.model_validate(row) for row in rows]

def upsert(session:Session,actor:Actor,settings:Settings,endpoint_id:str|None,data:WebhookEndpointWrite)->WebhookEndpointRead:
    actor.require('admin');validate_url(data.url,settings)
    row=session.get(WebhookEndpoint,endpoint_id) if endpoint_id else None
    if endpoint_id and row is None:raise AppError(404,'webhook_missing','Webhook endpoint is not available.')
    if row is None:
        if data.revision is not None:raise AppError(409,'revision_conflict','Webhook endpoint does not exist yet.')
        row=WebhookEndpoint(id=str(uuid4()),name=data.name,url=data.url,topics=data.topics,secret_ref=data.secret_ref,enabled=data.enabled,revision=1,created_by=actor.user_id,created_at=utcnow(),updated_at=utcnow());session.add(row)
    else:
        if data.revision!=row.revision:raise AppError(409,'revision_conflict','Webhook endpoint changed. Refresh and retry.',{'current_revision':row.revision})
        row.name=data.name;row.url=data.url;row.topics=data.topics;row.secret_ref=data.secret_ref;row.enabled=data.enabled;row.revision+=1;row.updated_at=utcnow()
    session.flush();return WebhookEndpointRead.model_validate(row)

def delivery_request(row:WebhookEndpoint,topic:str,payload:dict,timestamp:int)->tuple[bytes,dict[str,str]]:
    if topic not in row.topics:raise AppError(422,'webhook_topic_not_subscribed','Webhook endpoint is not subscribed to this topic.')
    body=json.dumps({'topic':topic,'event':payload},sort_keys=True,separators=(',',':')).encode()
    if len(body)>256_000:raise AppError(413,'webhook_payload_too_large','Webhook payload is too large.')
    secret=secret_for(row.secret_ref);signature=sign(secret,timestamp,body)
    return body,{'Content-Type':'application/json','X-Golden-Timestamp':str(timestamp),'X-Golden-Signature':'sha256='+signature}

def deliver(session:Session,settings:Settings,endpoint_id:str,event_id:str,*,client=None)->dict:
    """Deliver one durable event to a reviewed endpoint; redirects are never followed."""
    from app.platform.models import PlatformEvent
    endpoint=session.get(WebhookEndpoint,endpoint_id);event=session.scalar(select(PlatformEvent).where(PlatformEvent.event_id==event_id))
    if not endpoint or not endpoint.enabled:raise RuntimeError('Webhook endpoint is unavailable or disabled.')
    if not event:raise RuntimeError('Platform event is unavailable.')
    delivery=session.scalar(select(WebhookDelivery).where(WebhookDelivery.endpoint_id==endpoint_id,WebhookDelivery.event_id==event_id))
    if delivery is None:
        delivery=WebhookDelivery(id=str(uuid4()),endpoint_id=endpoint_id,event_id=event_id,status='pending',attempts=0,created_at=utcnow(),updated_at=utcnow());session.add(delivery)
    delivery.status='delivering';delivery.attempts+=1;delivery.last_error=None;delivery.updated_at=utcnow();session.flush()
    try:
        validate_url(endpoint.url,settings)
        import time
        timestamp=int(time.time());body,headers=delivery_request(endpoint,event.topic,{'event_id':event.event_id,'sequence':event.sequence,'entity_type':event.entity_type,'entity_id':event.entity_id,'payload':event.payload,'created_at':event.created_at.isoformat()},timestamp)
        if client is None:
            import httpx
            with httpx.Client(timeout=10,follow_redirects=False,trust_env=False) as owned:
                response=owned.post(endpoint.url,content=body,headers=headers)
        else:response=client.post(endpoint.url,content=body,headers=headers)
        delivery.response_status=int(response.status_code)
        if response.status_code<200 or response.status_code>=300:
            delivery.status='retrying';delivery.response_summary=f'HTTP {response.status_code}';delivery.last_error='non_success_response';delivery.updated_at=utcnow();session.flush()
            raise RuntimeError(f'Webhook delivery returned HTTP {response.status_code}.')
        delivery.status='delivered';delivery.response_summary=f'HTTP {response.status_code}';delivery.updated_at=utcnow();session.flush()
        return {'status_code':response.status_code,'endpoint_id':endpoint.id,'event_id':event.event_id,'delivery_id':delivery.id,'attempts':delivery.attempts}
    except RuntimeError:
        raise
    except Exception:
        delivery.status='retrying';delivery.last_error='delivery_failed';delivery.updated_at=utcnow();session.flush()
        raise RuntimeError('Webhook delivery failed; the durable job may retry it.') from None
