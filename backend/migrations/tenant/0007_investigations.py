from alembic import op
import sqlalchemy as sa
revision='tenant_0007'
down_revision='tenant_0006'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('investigations',sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.String(200),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('priority',sa.String(80),nullable=False),sa.Column('problem',sa.String(20000),nullable=False),sa.Column('evidence',sa.JSON,nullable=False),sa.Column('hypotheses',sa.JSON,nullable=False),sa.Column('causes',sa.JSON,nullable=False),sa.Column('actions',sa.JSON,nullable=False),sa.Column('findings',sa.String(60000),nullable=True),sa.Column('conclusion',sa.String(60000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_investigations_title_required'),sa.CheckConstraint("status IN ('open','investigating','validated','resolved','closed')",name='ck_investigations_status'),sa.CheckConstraint("priority IN ('low','medium','high','critical')",name='ck_investigations_priority'),sa.CheckConstraint('length(trim(problem)) BETWEEN 1 AND 20000',name='ck_investigations_problem_required'),sa.CheckConstraint('revision >= 1',name='ck_investigations_revision'))
    op.create_index('ix_investigations_archived','investigations',['archived'])
    op.create_index('ix_investigations_priority','investigations',['priority'])
    op.create_index('ix_investigations_status','investigations',['status'])
    op.create_index('ix_investigations_title','investigations',['title'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
