from __future__ import annotations
from uuid import uuid4
from app.platform.database import Database
from app.platform.policy import load_policy
from app.platform.errors import AppError
from app.platform.models import Membership, Tenant
from app.platform.security import Actor
from app.platform.transactions import write_transaction
from app.profiles.company.identity import CompanyIdentity, DevelopmentIdentity
from app.features.work_items.schemas import WorkItemCreate
from app.features.work_items.service import create_item

def trusted_actor(database: Database, tenant_id: str) -> Actor:
    # This trusted tool only creates work items; it does not expose attachment
    # uploads. Production ASGI startup/preflight still requires scanner status.
    database.settings.assert_maintenance_safe()
    provider=CompanyIdentity() if database.settings.profile=='company' else DevelopmentIdentity(database.settings.dev_user)
    user=provider.current_user()
    with database.session() as session:
        member=session.get(Membership,(tenant_id,user));tenant=session.get(Tenant,tenant_id)
        if not member or not tenant or not tenant.active:
            raise AppError(403,'tenant_forbidden','The script identity has no access to this tenant.')
        return Actor(user,tenant_id,member.role,str(uuid4()),load_policy(database.settings.policy_config).permissions(member.role))

def create_work_item_direct(database: Database,tenant_id: str,data: WorkItemCreate):
    """Trusted tooling, same domain service and atomic audit as the HTTP route.

    Arbitrary disk access bypasses application authorization. Restrict OS access;
    this adapter cannot secure raw sqlite3 clients or coordinate unsafe mounts.
    """
    actor=trusted_actor(database,tenant_id)
    with write_transaction(database,tenant_id) as session:
        return create_item(session,actor,data)
