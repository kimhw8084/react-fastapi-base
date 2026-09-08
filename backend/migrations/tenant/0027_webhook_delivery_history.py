from alembic import op
import sqlalchemy as sa

revision='tenant_0027'
down_revision='tenant_0026'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('webhook_deliveries',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('endpoint_id',sa.String(36),nullable=False),sa.Column('event_id',sa.String(36),nullable=False),
        sa.Column('status',sa.String(20),nullable=False),sa.Column('attempts',sa.Integer(),nullable=False),sa.Column('response_status',sa.Integer(),nullable=True),
        sa.Column('response_summary',sa.String(240),nullable=True),sa.Column('last_error',sa.String(240),nullable=True),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('endpoint_id','event_id',name='uq_webhook_deliveries_endpoint_event'),sa.CheckConstraint("status IN ('pending','delivering','retrying','delivered','failed')",name='ck_webhook_deliveries_status'),sa.CheckConstraint('attempts >= 0',name='ck_webhook_deliveries_attempts'))
    op.create_index('ix_webhook_deliveries_endpoint_id','webhook_deliveries',['endpoint_id'])
    op.create_index('ix_webhook_deliveries_event_id','webhook_deliveries',['event_id'])
    op.create_index('ix_webhook_deliveries_status','webhook_deliveries',['status'])

def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
