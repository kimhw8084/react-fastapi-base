from alembic import op
import sqlalchemy as sa
revision='tenant_0010'
down_revision='tenant_0009'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('plan_tasks',sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.String(200),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('start_date',sa.Date,nullable=False),sa.Column('end_date',sa.Date,nullable=False),sa.Column('baseline_start',sa.Date,nullable=True),sa.Column('baseline_end',sa.Date,nullable=True),sa.Column('progress',sa.Float,nullable=False),sa.Column('milestone',sa.Boolean,nullable=False),sa.Column('owner',sa.String(160),nullable=True),sa.Column('duration_days',sa.Integer,nullable=False),sa.Column('notes',sa.String(20000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_plan_tasks_title_required'),sa.CheckConstraint("status IN ('planned','ready','in_progress','blocked','done','cancelled')",name='ck_plan_tasks_status'),sa.CheckConstraint('progress >= 0',name='ck_plan_tasks_progress_minimum'),sa.CheckConstraint('progress <= 100',name='ck_plan_tasks_progress_maximum'),sa.CheckConstraint('duration_days >= 1',name='ck_plan_tasks_duration_days_minimum'),sa.CheckConstraint('duration_days <= 3650',name='ck_plan_tasks_duration_days_maximum'),sa.CheckConstraint('revision >= 1',name='ck_plan_tasks_revision'))
    op.create_index('ix_plan_tasks_archived','plan_tasks',['archived'])
    op.create_index('ix_plan_tasks_baseline_end','plan_tasks',['baseline_end'])
    op.create_index('ix_plan_tasks_baseline_start','plan_tasks',['baseline_start'])
    op.create_index('ix_plan_tasks_duration_days','plan_tasks',['duration_days'])
    op.create_index('ix_plan_tasks_end_date','plan_tasks',['end_date'])
    op.create_index('ix_plan_tasks_milestone','plan_tasks',['milestone'])
    op.create_index('ix_plan_tasks_owner','plan_tasks',['owner'])
    op.create_index('ix_plan_tasks_progress','plan_tasks',['progress'])
    op.create_index('ix_plan_tasks_start_date','plan_tasks',['start_date'])
    op.create_index('ix_plan_tasks_status','plan_tasks',['status'])
    op.create_index('ix_plan_tasks_title','plan_tasks',['title'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
