from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from app.platform.database import Database

BACKEND_ROOT = Path(__file__).resolve().parents[2]
def expected_revision(role: str) -> str:
    config=Config(str(BACKEND_ROOT/'alembic.ini'))
    config.set_main_option('script_location',str(BACKEND_ROOT/'migrations'))
    config.set_main_option('version_locations',str(BACKEND_ROOT/'migrations'/role))
    head=ScriptDirectory.from_config(config).get_current_head()
    if head is None:raise RuntimeError('Migration history is empty.')
    return head

def migrate(database: Database, tenant_id: str | None = None) -> None:
    role = 'tenant' if tenant_id else 'registry'
    config = Config(str(BACKEND_ROOT/'alembic.ini'))
    config.set_main_option('script_location',str(BACKEND_ROOT/'migrations'))
    config.set_main_option('version_locations',str(BACKEND_ROOT/'migrations'/role))
    with database.engine(tenant_id, provision=True).begin() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config,'head')
    path = database.path(tenant_id)
    path.chmod(0o600)
    # Dispose provisioning URL so normal accesses use mode=rw, never mode=rwc.
    database.close()

def assert_revision(database: Database, tenant_id: str | None = None) -> None:
    role = 'tenant' if tenant_id else 'registry'
    with database.session(tenant_id) as session:
        actual = session.execute(text('SELECT version_num FROM alembic_version')).scalar_one()
        if actual != expected_revision(role):
            raise RuntimeError('Database migration is required.')
