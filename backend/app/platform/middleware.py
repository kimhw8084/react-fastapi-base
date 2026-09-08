from __future__ import annotations
import json
import logging
import time
from collections import defaultdict, deque
from uuid import uuid4

logger=logging.getLogger('golden.http')

class RequestSafetyMiddleware:
    """Bounded body buffering and admission control; never logs request bodies."""
    def __init__(self,app,settings):
        self.app=app;self.settings=settings
        self.buckets: dict[str, deque] = {}

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':
            return await self.app(scope,receive,send)
        request_id=str(uuid4());started=time.monotonic()
        scope.setdefault('state',{})['request_id']=request_id
        headers={key.lower():value for key,value in scope.get('headers',[])}
        async def reject(status,code,message):
            body=json.dumps({'error':{'code':code,'message':message,'request_id':request_id,'details':None}}).encode()
            await send({'type':'http.response.start','status':status,'headers':[(b'content-type',b'application/json'),(b'x-request-id',request_id.encode()),(b'cache-control',b'no-store')]})
            await send({'type':'http.response.body','body':body})
        if scope.get('path','').startswith('/api/'):
            key=(scope.get('client') or ('unknown',0))[0]
            # No forwarding headers are trusted for admission keys.
            now=time.monotonic()
            if len(self.buckets)>4096:
                self.buckets={k:q for k,q in self.buckets.items() if q and q[-1]>now-60}
                if len(self.buckets)>4096:
                    return await reject(503,'admission_full','Try again shortly.')
            q=self.buckets.setdefault(key,deque())
            while q and q[0]<now-60:q.popleft()
            if len(q)>=self.settings.request_limit_per_minute:
                return await reject(429,'rate_limited','Request limit reached; try again in a minute.')
            q.append(now)
        body=bytearray()
        while True:
            event=await receive()
            if event['type']=='http.disconnect':return
            body.extend(event.get('body',b''))
            if len(body)>self.settings.max_request_bytes:
                return await reject(413,'request_too_large','The request body exceeds the supported limit.')
            if not event.get('more_body',False):break
        if scope['method'] in ('POST','PUT','PATCH') and body and not headers.get(b'content-type',b'').lower().startswith(b'application/json'):
            return await reject(415,'json_required','Use application/json for API writes.')
        consumed=False
        async def replay():
            nonlocal consumed
            if not consumed:
                consumed=True
                return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        status_code=500
        async def safe_send(message):
            nonlocal status_code
            if message['type']=='http.response.start':
                status_code=message['status']
                values=list(message.get('headers',[]))
                values.extend([(b'x-request-id',request_id.encode()),(b'x-content-type-options',b'nosniff'),(b'referrer-policy',b'no-referrer'),(b'cache-control',b'no-store')])
                message={**message,'headers':values}
            await send(message)
        try:
            await self.app(scope,replay,safe_send)
        finally:
            logger.info(json.dumps({'event':'request','request_id':request_id,'method':scope['method'],'status':status_code,'duration_ms':round((time.monotonic()-started)*1000,1)}))
