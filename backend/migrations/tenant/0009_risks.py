from alembic import op
import sqlalchemy as sa
revision='tenant_0009'
down_revision='tenant_0008'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('risks',sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.String(200),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('category',sa.String(80),nullable=False),sa.Column('severity',sa.Integer,nullable=False),sa.Column('occurrence',sa.Integer,nullable=False),sa.Column('detection',sa.Integer,nullable=False),sa.Column('rpn',sa.Integer,nullable=False),sa.Column('residual_severity',sa.Integer,nullable=True),sa.Column('residual_occurrence',sa.Integer,nullable=True),sa.Column('residual_detection',sa.Integer,nullable=True),sa.Column('residual_rpn',sa.Integer,nullable=True),sa.Column('effect',sa.String(20000),nullable=True),sa.Column('causes',sa.JSON,nullable=False),sa.Column('mitigations',sa.JSON,nullable=False),sa.Column('prevention',sa.JSON,nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_risks_title_required'),sa.CheckConstraint("status IN ('identified','assessing','mitigating','monitoring','closed')",name='ck_risks_status'),sa.CheckConstraint("category IN ('design','process','hardware','software','network','human','environment')",name='ck_risks_category'),sa.CheckConstraint('severity >= 1',name='ck_risks_severity_minimum'),sa.CheckConstraint('severity <= 10',name='ck_risks_severity_maximum'),sa.CheckConstraint('occurrence >= 1',name='ck_risks_occurrence_minimum'),sa.CheckConstraint('occurrence <= 10',name='ck_risks_occurrence_maximum'),sa.CheckConstraint('detection >= 1',name='ck_risks_detection_minimum'),sa.CheckConstraint('detection <= 10',name='ck_risks_detection_maximum'),sa.CheckConstraint('rpn >= 1',name='ck_risks_rpn_minimum'),sa.CheckConstraint('rpn <= 1000',name='ck_risks_rpn_maximum'),sa.CheckConstraint('residual_severity >= 1',name='ck_risks_residual_severity_minimum'),sa.CheckConstraint('residual_severity <= 10',name='ck_risks_residual_severity_maximum'),sa.CheckConstraint('residual_occurrence >= 1',name='ck_risks_residual_occurrence_minimum'),sa.CheckConstraint('residual_occurrence <= 10',name='ck_risks_residual_occurrence_maximum'),sa.CheckConstraint('residual_detection >= 1',name='ck_risks_residual_detection_minimum'),sa.CheckConstraint('residual_detection <= 10',name='ck_risks_residual_detection_maximum'),sa.CheckConstraint('residual_rpn >= 1',name='ck_risks_residual_rpn_minimum'),sa.CheckConstraint('residual_rpn <= 1000',name='ck_risks_residual_rpn_maximum'),sa.CheckConstraint('revision >= 1',name='ck_risks_revision'))
    op.create_index('ix_risks_archived','risks',['archived'])
    op.create_index('ix_risks_category','risks',['category'])
    op.create_index('ix_risks_detection','risks',['detection'])
    op.create_index('ix_risks_occurrence','risks',['occurrence'])
    op.create_index('ix_risks_residual_detection','risks',['residual_detection'])
    op.create_index('ix_risks_residual_occurrence','risks',['residual_occurrence'])
    op.create_index('ix_risks_residual_rpn','risks',['residual_rpn'])
    op.create_index('ix_risks_residual_severity','risks',['residual_severity'])
    op.create_index('ix_risks_rpn','risks',['rpn'])
    op.create_index('ix_risks_severity','risks',['severity'])
    op.create_index('ix_risks_status','risks',['status'])
    op.create_index('ix_risks_title','risks',['title'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
