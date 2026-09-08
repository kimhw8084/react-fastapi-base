from alembic import op
import sqlalchemy as sa
revision='tenant_0017'
down_revision='tenant_0016'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('process_recipes',sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(160),nullable=False),sa.Column('version_name',sa.String(80),nullable=False),sa.Column('process',sa.String(160),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('parameters',sa.JSON,nullable=False),sa.Column('limits',sa.JSON,nullable=False),sa.Column('approved_by',sa.String(160),nullable=True),sa.Column('approved_at',sa.DateTime(timezone=True),nullable=True),sa.Column('notes',sa.String(50000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(name)) BETWEEN 1 AND 160',name='ck_process_recipes_name_required'),sa.CheckConstraint('length(trim(version_name)) BETWEEN 1 AND 80',name='ck_process_recipes_version_name_required'),sa.CheckConstraint('length(trim(process)) BETWEEN 1 AND 160',name='ck_process_recipes_process_required'),sa.CheckConstraint("status IN ('draft','qualified','released','deprecated')",name='ck_process_recipes_status'),sa.CheckConstraint('revision >= 1',name='ck_process_recipes_revision'))
    op.create_index('ix_process_recipes_approved_at','process_recipes',['approved_at'])
    op.create_index('ix_process_recipes_approved_by','process_recipes',['approved_by'])
    op.create_index('ix_process_recipes_archived','process_recipes',['archived'])
    op.create_index('ix_process_recipes_name','process_recipes',['name'])
    op.create_index('ix_process_recipes_process','process_recipes',['process'])
    op.create_index('ix_process_recipes_status','process_recipes',['status'])
    op.create_index('ix_process_recipes_version_name','process_recipes',['version_name'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
