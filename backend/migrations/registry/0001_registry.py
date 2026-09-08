from alembic import op
import sqlalchemy as sa
revision = 'registry_0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('tenants', sa.Column('id',sa.String(36),primary_key=True), sa.Column('name',sa.String(120),nullable=False,unique=True), sa.Column('active',sa.Boolean(),nullable=False))
    op.create_table('memberships',sa.Column('tenant_id',sa.String(36),sa.ForeignKey('tenants.id'),primary_key=True),sa.Column('user_id',sa.String(200),primary_key=True),sa.Column('role',sa.String(20),nullable=False),sa.CheckConstraint("role IN ('admin','editor','viewer')",name='ck_membership_role'))

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
