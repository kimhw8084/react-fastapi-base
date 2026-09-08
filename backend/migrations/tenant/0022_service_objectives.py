from alembic import op
import sqlalchemy as sa
revision='tenant_0022'
down_revision='tenant_0021'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('service_objectives',sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(200),nullable=False),sa.Column('window_days',sa.Integer,nullable=False),sa.Column('target_percent',sa.Float,nullable=False),sa.Column('current_percent',sa.Float,nullable=False),sa.Column('error_budget_remaining',sa.Float,nullable=False),sa.Column('burn_rate',sa.Float,nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('notes',sa.String(30000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(name)) BETWEEN 1 AND 200',name='ck_service_objectives_name_required'),sa.CheckConstraint('window_days >= 1',name='ck_service_objectives_window_days_minimum'),sa.CheckConstraint('window_days <= 365',name='ck_service_objectives_window_days_maximum'),sa.CheckConstraint('target_percent >= 0.001',name='ck_service_objectives_target_percent_minimum'),sa.CheckConstraint('target_percent <= 100',name='ck_service_objectives_target_percent_maximum'),sa.CheckConstraint('current_percent >= 0',name='ck_service_objectives_current_percent_minimum'),sa.CheckConstraint('current_percent <= 100',name='ck_service_objectives_current_percent_maximum'),sa.CheckConstraint('error_budget_remaining >= 0',name='ck_service_objectives_error_budget_remaining_minimum'),sa.CheckConstraint('error_budget_remaining <= 100',name='ck_service_objectives_error_budget_remaining_maximum'),sa.CheckConstraint('burn_rate >= 0',name='ck_service_objectives_burn_rate_minimum'),sa.CheckConstraint("status IN ('healthy','warning','exhausted')",name='ck_service_objectives_status'),sa.CheckConstraint('revision >= 1',name='ck_service_objectives_revision'))
    op.create_index('ix_service_objectives_archived','service_objectives',['archived'])
    op.create_index('ix_service_objectives_burn_rate','service_objectives',['burn_rate'])
    op.create_index('ix_service_objectives_current_percent','service_objectives',['current_percent'])
    op.create_index('ix_service_objectives_error_budget_remaining','service_objectives',['error_budget_remaining'])
    op.create_index('ix_service_objectives_name','service_objectives',['name'])
    op.create_index('ix_service_objectives_status','service_objectives',['status'])
    op.create_index('ix_service_objectives_target_percent','service_objectives',['target_percent'])
    op.create_index('ix_service_objectives_window_days','service_objectives',['window_days'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
