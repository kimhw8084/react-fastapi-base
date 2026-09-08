from alembic import op
import sqlalchemy as sa
revision='tenant_0011'
down_revision='tenant_0010'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('diagram_documents',sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.String(200),nullable=False),sa.Column('diagram_type',sa.String(80),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('nodes',sa.JSON,nullable=False),sa.Column('edges',sa.JSON,nullable=False),sa.Column('viewport',sa.JSON,nullable=False),sa.Column('node_count',sa.Integer,nullable=False),sa.Column('edge_count',sa.Integer,nullable=False),sa.Column('notes',sa.String(50000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_diagram_documents_title_required'),sa.CheckConstraint("diagram_type IN ('architecture','workflow','data_flow','topology','process','state_machine','lineage')",name='ck_diagram_documents_diagram_type'),sa.CheckConstraint("status IN ('draft','active','in_review','retired')",name='ck_diagram_documents_status'),sa.CheckConstraint('node_count >= 0',name='ck_diagram_documents_node_count_minimum'),sa.CheckConstraint('node_count <= 1000',name='ck_diagram_documents_node_count_maximum'),sa.CheckConstraint('edge_count >= 0',name='ck_diagram_documents_edge_count_minimum'),sa.CheckConstraint('edge_count <= 3000',name='ck_diagram_documents_edge_count_maximum'),sa.CheckConstraint('revision >= 1',name='ck_diagram_documents_revision'))
    op.create_index('ix_diagram_documents_archived','diagram_documents',['archived'])
    op.create_index('ix_diagram_documents_diagram_type','diagram_documents',['diagram_type'])
    op.create_index('ix_diagram_documents_edge_count','diagram_documents',['edge_count'])
    op.create_index('ix_diagram_documents_node_count','diagram_documents',['node_count'])
    op.create_index('ix_diagram_documents_status','diagram_documents',['status'])
    op.create_index('ix_diagram_documents_title','diagram_documents',['title'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
