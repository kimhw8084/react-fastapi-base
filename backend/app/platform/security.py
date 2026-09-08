from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import time
from fastapi import Request
from sqlalchemy import select
from app.platform.errors import AppError
from app.platform.models import Membership, Tenant

@dataclass(frozen=True)
class Actor:
    user_id: str
    tenant_id: str
    role: str
    request_id: str
    permissions: frozenset[str]

    def require(self, permission: str) -> None:
        if permission not in self.permissions:
            raise AppError(403, 'forbidden', 'You do not have permission for this action.')

def csrf_token(secret: str, user_id: str, hour: int | None = None) -> str:
    hour = int(time.time() // 3600) if hour is None else hour
    message = f'{hour}:{user_id}'.encode()
    return f'{hour}.{hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()}'

def valid_csrf(secret: str, user_id: str, token: str) -> bool:
    if not token.isascii() or len(token) > 96:
        return False
    now = int(time.time() // 3600)
    return any(hmac.compare_digest(token, csrf_token(secret, user_id, hour)) for hour in (now, now-1))

def actor_for(request: Request) -> Actor:
    user_id = request.app.state.identity.current_user()
    tenant_id = request.headers.get('X-Tenant-Id', '')
    if not tenant_id:
        raise AppError(400, 'tenant_required', 'Select a tenant before opening a workspace.')
    request.app.state.database.path(tenant_id)
    with request.app.state.database.session() as db:
        membership = db.get(Membership, (tenant_id, user_id))
        tenant = db.get(Tenant, tenant_id)
        if not tenant or not tenant.active or not membership:
            raise AppError(403, 'tenant_forbidden', 'This tenant is not accessible.')
        actor = Actor(user_id, tenant_id, membership.role, request.state.request_id, request.app.state.policy.permissions(membership.role))
    actor.require('read')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        if origin is not None and origin not in request.app.state.settings.allowed_origins:
            raise AppError(403, 'origin_forbidden', 'Request origin is not allowed.')
        if not valid_csrf(request.app.state.csrf_secret, user_id, request.headers.get('X-CSRF-Token', '')):
            raise AppError(403, 'csrf_failed', 'Refresh the application before retrying this action.')
    return actor
