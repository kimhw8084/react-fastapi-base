from alembic import op
import sqlalchemy as sa
revision='tenant_0019'
down_revision='tenant_0018'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('delivery_runs',sa.Column('id',sa.String(36),primary_key=True),sa.Column('run_id',sa.String(120),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('environment',sa.String(80),nullable=False),sa.Column('commit_sha',sa.String(80),nullable=True),sa.Column('branch',sa.String(160),nullable=True),sa.Column('started_at',sa.DateTime(timezone=True),nullable=False),sa.Column('completed_at',sa.DateTime(timezone=True),nullable=True),sa.Column('duration_minutes',sa.Float,nullable=False),sa.Column('stages',sa.JSON,nullable=False),sa.Column('artifacts',sa.JSON,nullable=False),sa.Column('triggered_by',sa.String(160),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(run_id)) BETWEEN 1 AND 120',name='ck_delivery_runs_run_id_required'),sa.CheckConstraint("status IN ('queued','running','passed','failed','cancelled')",name='ck_delivery_runs_status'),sa.CheckConstraint("environment IN ('development','test','staging','production')",name='ck_delivery_runs_environment'),sa.CheckConstraint('duration_minutes >= 0',name='ck_delivery_runs_duration_minutes_minimum'),sa.CheckConstraint('revision >= 1',name='ck_delivery_runs_revision'))
    op.create_index('ix_delivery_runs_archived','delivery_runs',['archived'])
    op.create_index('ix_delivery_runs_branch','delivery_runs',['branch'])
    op.create_index('ix_delivery_runs_commit_sha','delivery_runs',['commit_sha'])
    op.create_index('ix_delivery_runs_completed_at','delivery_runs',['completed_at'])
    op.create_index('ix_delivery_runs_duration_minutes','delivery_runs',['duration_minutes'])
    op.create_index('ix_delivery_runs_environment','delivery_runs',['environment'])
    op.create_index('ix_delivery_runs_run_id','delivery_runs',['run_id'])
    op.create_index('ix_delivery_runs_started_at','delivery_runs',['started_at'])
    op.create_index('ix_delivery_runs_status','delivery_runs',['status'])
    op.create_index('ix_delivery_runs_triggered_by','delivery_runs',['triggered_by'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
