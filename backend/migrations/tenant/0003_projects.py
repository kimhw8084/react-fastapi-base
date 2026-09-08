from alembic import op
import sqlalchemy as sa
revision='tenant_0003'
down_revision='tenant_0002'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('projects',
      sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.String(160),nullable=False),
      sa.Column('summary',sa.Text(),nullable=False),sa.Column('status',sa.String(20),nullable=False),
      sa.Column('owner',sa.String(120),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),
      sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),
      sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
      sa.CheckConstraint("status IN ('planned','active','blocked','complete')",name='ck_project_status'),
      sa.CheckConstraint('revision >= 1',name='ck_project_revision'),
      sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 160',name='ck_project_title'))
    for field in ('title','status','owner','archived'):op.create_index(f'ix_projects_{field}','projects',[field])

def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
