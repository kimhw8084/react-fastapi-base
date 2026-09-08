from alembic import op
import sqlalchemy as sa
revision='tenant_0023'
down_revision='tenant_0022'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('durable_jobs',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('job_type',sa.String(80),nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('payload',sa.JSON(),nullable=False),sa.Column('result',sa.JSON(),nullable=True),sa.Column('error',sa.Text(),nullable=True),sa.Column('attempts',sa.Integer(),nullable=False),sa.Column('max_attempts',sa.Integer(),nullable=False),sa.Column('run_after',sa.DateTime(timezone=True),nullable=False),sa.Column('lease_owner',sa.String(120),nullable=True),sa.Column('lease_expires_at',sa.DateTime(timezone=True),nullable=True),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.CheckConstraint("status IN ('queued','running','succeeded','failed','cancelled')",name='ck_durable_jobs_status'),sa.CheckConstraint('attempts >= 0',name='ck_durable_jobs_attempts'),sa.CheckConstraint('max_attempts BETWEEN 1 AND 20',name='ck_durable_jobs_max_attempts'))
    for col in ('job_type','status','run_after','created_by'):op.create_index(f'ix_durable_jobs_{col}','durable_jobs',[col])
    op.create_table('platform_events',sa.Column('sequence',sa.Integer(),primary_key=True,autoincrement=True),sa.Column('event_id',sa.String(36),nullable=False,unique=True),sa.Column('topic',sa.String(100),nullable=False),sa.Column('entity_type',sa.String(60),nullable=True),sa.Column('entity_id',sa.String(64),nullable=True),sa.Column('payload',sa.JSON(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    for col in ('event_id','topic','entity_type','entity_id','created_at'):op.create_index(f'ix_platform_events_{col}','platform_events',[col])
    op.create_table('notifications',sa.Column('id',sa.String(36),primary_key=True),sa.Column('user_id',sa.String(200),nullable=False),sa.Column('kind',sa.String(60),nullable=False),sa.Column('title',sa.String(180),nullable=False),sa.Column('body',sa.String(2000),nullable=False),sa.Column('data',sa.JSON(),nullable=False),sa.Column('read_at',sa.DateTime(timezone=True),nullable=True),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    for col in ('user_id','kind','read_at','created_at'):op.create_index(f'ix_notifications_{col}','notifications',[col])
    op.create_table('notification_preferences',sa.Column('user_id',sa.String(200),primary_key=True),sa.Column('kind',sa.String(60),primary_key=True),sa.Column('enabled',sa.Boolean(),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('revision >= 1',name='ck_notification_preferences_revision'))
    op.create_table('feature_flags',sa.Column('key',sa.String(80),primary_key=True),sa.Column('enabled',sa.Boolean(),nullable=False),sa.Column('description',sa.String(300),nullable=False),sa.Column('rules',sa.JSON(),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('updated_by',sa.String(200),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('revision >= 1',name='ck_feature_flags_revision'))
    op.create_table('webhook_endpoints',sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(120),nullable=False),sa.Column('url',sa.String(500),nullable=False),sa.Column('topics',sa.JSON(),nullable=False),sa.Column('secret_ref',sa.String(80),nullable=False),sa.Column('enabled',sa.Boolean(),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('revision >= 1',name='ck_webhook_endpoints_revision'))
    op.create_index('ix_webhook_endpoints_enabled','webhook_endpoints',['enabled'])
    op.create_table('webhook_receipts',sa.Column('endpoint_id',sa.String(36),primary_key=True),sa.Column('external_event_id',sa.String(120),primary_key=True),sa.Column('received_at',sa.DateTime(timezone=True),nullable=False))

def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
