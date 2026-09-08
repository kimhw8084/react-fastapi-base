from alembic import op
import sqlalchemy as sa
revision='tenant_0018'
down_revision='tenant_0017'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('software_services',sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(160),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('tier',sa.String(80),nullable=False),sa.Column('owner',sa.String(160),nullable=True),sa.Column('repository',sa.String(500),nullable=True),sa.Column('runtime',sa.String(120),nullable=True),sa.Column('environment',sa.String(80),nullable=False),sa.Column('config',sa.JSON,nullable=False),sa.Column('description',sa.String(50000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(name)) BETWEEN 1 AND 160',name='ck_software_services_name_required'),sa.CheckConstraint("status IN ('healthy','degraded','maintenance','retired')",name='ck_software_services_status'),sa.CheckConstraint("tier IN ('tier_0','tier_1','tier_2','tier_3')",name='ck_software_services_tier'),sa.CheckConstraint("environment IN ('development','test','staging','production')",name='ck_software_services_environment'),sa.CheckConstraint('revision >= 1',name='ck_software_services_revision'))
    op.create_index('ix_software_services_archived','software_services',['archived'])
    op.create_index('ix_software_services_environment','software_services',['environment'])
    op.create_index('ix_software_services_name','software_services',['name'])
    op.create_index('ix_software_services_owner','software_services',['owner'])
    op.create_index('ix_software_services_repository','software_services',['repository'])
    op.create_index('ix_software_services_runtime','software_services',['runtime'])
    op.create_index('ix_software_services_status','software_services',['status'])
    op.create_index('ix_software_services_tier','software_services',['tier'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
