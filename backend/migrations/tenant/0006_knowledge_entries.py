from alembic import op
import sqlalchemy as sa
revision='tenant_0006'
down_revision='tenant_0005'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('knowledge_entries',sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.String(200),nullable=False),sa.Column('entry_type',sa.String(80),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('criticality',sa.String(80),nullable=False),sa.Column('owner',sa.String(160),nullable=True),sa.Column('review_state',sa.String(80),nullable=False),sa.Column('next_review_at',sa.Date,nullable=True),sa.Column('content',sa.String(100000),nullable=True),sa.Column('procedures',sa.JSON,nullable=False),sa.Column('tags',sa.JSON,nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_knowledge_entries_title_required'),sa.CheckConstraint("entry_type IN ('runbook','procedure','troubleshooting','architecture_note','lesson','standard','faq')",name='ck_knowledge_entries_entry_type'),sa.CheckConstraint("status IN ('draft','published','archived_reference')",name='ck_knowledge_entries_status'),sa.CheckConstraint("criticality IN ('standard','critical')",name='ck_knowledge_entries_criticality'),sa.CheckConstraint("review_state IN ('needs_review','verified','stale','deprecated','emergency_only')",name='ck_knowledge_entries_review_state'),sa.CheckConstraint('revision >= 1',name='ck_knowledge_entries_revision'))
    op.create_index('ix_knowledge_entries_archived','knowledge_entries',['archived'])
    op.create_index('ix_knowledge_entries_criticality','knowledge_entries',['criticality'])
    op.create_index('ix_knowledge_entries_entry_type','knowledge_entries',['entry_type'])
    op.create_index('ix_knowledge_entries_next_review_at','knowledge_entries',['next_review_at'])
    op.create_index('ix_knowledge_entries_owner','knowledge_entries',['owner'])
    op.create_index('ix_knowledge_entries_review_state','knowledge_entries',['review_state'])
    op.create_index('ix_knowledge_entries_status','knowledge_entries',['status'])
    op.create_index('ix_knowledge_entries_title','knowledge_entries',['title'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
