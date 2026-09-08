from alembic import op
import sqlalchemy as sa
revision='tenant_0008'
down_revision='tenant_0007'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('research',sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.String(200),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('phase',sa.String(80),nullable=False),sa.Column('question',sa.String(20000),nullable=False),sa.Column('hypothesis',sa.String(60000),nullable=True),sa.Column('methodology',sa.String(60000),nullable=True),sa.Column('experiments',sa.JSON,nullable=False),sa.Column('evidence',sa.JSON,nullable=False),sa.Column('analysis',sa.String(80000),nullable=True),sa.Column('findings',sa.String(80000),nullable=True),sa.Column('conclusion',sa.String(60000),nullable=True),sa.Column('recommendation',sa.String(60000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_research_title_required'),sa.CheckConstraint("status IN ('question','researching','experimenting','analyzing','review','complete')",name='ck_research_status'),sa.CheckConstraint("phase IN ('discovery','hypothesis','experiment','analysis','conclusion')",name='ck_research_phase'),sa.CheckConstraint('length(trim(question)) BETWEEN 1 AND 20000',name='ck_research_question_required'),sa.CheckConstraint('revision >= 1',name='ck_research_revision'))
    op.create_index('ix_research_archived','research',['archived'])
    op.create_index('ix_research_phase','research',['phase'])
    op.create_index('ix_research_status','research',['status'])
    op.create_index('ix_research_title','research',['title'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
