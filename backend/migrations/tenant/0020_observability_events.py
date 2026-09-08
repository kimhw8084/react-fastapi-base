from alembic import op
import sqlalchemy as sa
revision='tenant_0020'
down_revision='tenant_0019'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('observability_events',sa.Column('id',sa.String(36),primary_key=True),sa.Column('event_id',sa.String(160),nullable=False),sa.Column('signal',sa.String(80),nullable=False),sa.Column('severity',sa.String(80),nullable=False),sa.Column('timestamp',sa.DateTime(timezone=True),nullable=False),sa.Column('duration_ms',sa.Float,nullable=True),sa.Column('trace_id',sa.String(160),nullable=True),sa.Column('span_id',sa.String(160),nullable=True),sa.Column('parent_span_id',sa.String(160),nullable=True),sa.Column('operation',sa.String(200),nullable=True),sa.Column('message',sa.String(30000),nullable=True),sa.Column('attributes',sa.JSON,nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(event_id)) BETWEEN 1 AND 160',name='ck_observability_events_event_id_required'),sa.CheckConstraint("signal IN ('log','trace','metric')",name='ck_observability_events_signal'),sa.CheckConstraint("severity IN ('debug','info','warning','error','critical')",name='ck_observability_events_severity'),sa.CheckConstraint('duration_ms >= 0',name='ck_observability_events_duration_ms_minimum'),sa.CheckConstraint('revision >= 1',name='ck_observability_events_revision'))
    op.create_index('ix_observability_events_archived','observability_events',['archived'])
    op.create_index('ix_observability_events_duration_ms','observability_events',['duration_ms'])
    op.create_index('ix_observability_events_event_id','observability_events',['event_id'])
    op.create_index('ix_observability_events_operation','observability_events',['operation'])
    op.create_index('ix_observability_events_severity','observability_events',['severity'])
    op.create_index('ix_observability_events_signal','observability_events',['signal'])
    op.create_index('ix_observability_events_span_id','observability_events',['span_id'])
    op.create_index('ix_observability_events_timestamp','observability_events',['timestamp'])
    op.create_index('ix_observability_events_trace_id','observability_events',['trace_id'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
