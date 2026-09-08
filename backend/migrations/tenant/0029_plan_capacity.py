from alembic import op
import sqlalchemy as sa

revision='tenant_0029'
down_revision='tenant_0028'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('plan_tasks',sa.Column('resource_group',sa.String(120),nullable=True))
    op.add_column('plan_tasks',sa.Column('effort_hours',sa.Float(),nullable=False,server_default='8'))
    op.add_column('plan_tasks',sa.Column('capacity_hours',sa.Float(),nullable=False,server_default='8'))
    op.create_index('ix_plan_tasks_resource_group','plan_tasks',['resource_group'])
    op.create_index('ix_plan_tasks_effort_hours','plan_tasks',['effort_hours'])
    op.create_index('ix_plan_tasks_capacity_hours','plan_tasks',['capacity_hours'])

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
