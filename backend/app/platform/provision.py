from uuid import uuid4
from sqlalchemy import select
from app.platform.database import Database
from app.platform.migrations import migrate
from app.platform.models import Tenant, Membership
from app.platform.policy import load_policy
from app.profiles.company.identity import normalize_username

def provision(database: Database, name: str, admin_user: str) -> str:
    admin_user=normalize_username(admin_user)
    if not name.strip() or len(name)>120:
        raise ValueError('Tenant name must be 1–120 characters.')
    migrate(database)
    with database.session() as session:
        existing=session.scalar(select(Tenant).where(Tenant.name==name))
        if existing:
            raise ValueError('Tenant already exists. Use add-member or migrate; provisioning never silently changes existing access.')
    tenant_id=str(uuid4())
    migrate(database,tenant_id)
    with database.session() as session:
        with session.begin():
            session.add(Tenant(id=tenant_id,name=name,active=True));session.flush()
            session.add(Membership(tenant_id=tenant_id,user_id=admin_user,role='admin'))
    return tenant_id

def add_member(database: Database, tenant_id: str, user_id: str, role: str) -> None:
    user_id=normalize_username(user_id)
    if role not in load_policy(database.settings.policy_config).roles:raise ValueError('Unknown role.')
    with database.session() as session:
        with session.begin():
            tenant=session.get(Tenant,tenant_id)
            if not tenant or not tenant.active:raise ValueError('Tenant is not active.')
            existing=session.get(Membership,(tenant_id,user_id))
            if existing:
                raise ValueError('Membership exists. This command never silently changes privileges.')
            session.add(Membership(tenant_id=tenant_id,user_id=user_id,role=role))
