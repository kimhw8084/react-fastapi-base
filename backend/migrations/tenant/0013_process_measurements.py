from alembic import op
import sqlalchemy as sa
revision='tenant_0013'
down_revision='tenant_0012'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('process_measurements',sa.Column('id',sa.String(36),primary_key=True),sa.Column('sample_label',sa.String(160),nullable=False),sa.Column('process',sa.String(160),nullable=False),sa.Column('metric',sa.String(160),nullable=False),sa.Column('value',sa.Float,nullable=False),sa.Column('unit',sa.String(32),nullable=True),sa.Column('sampled_at',sa.DateTime(timezone=True),nullable=False),sa.Column('subgroup',sa.String(80),nullable=True),sa.Column('target',sa.Float,nullable=True),sa.Column('lower_spec',sa.Float,nullable=True),sa.Column('upper_spec',sa.Float,nullable=True),sa.Column('lot',sa.String(120),nullable=True),sa.Column('category',sa.String(80),nullable=False),sa.Column('context',sa.JSON,nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(sample_label)) BETWEEN 1 AND 160',name='ck_process_measurements_sample_label_required'),sa.CheckConstraint('length(trim(process)) BETWEEN 1 AND 160',name='ck_process_measurements_process_required'),sa.CheckConstraint('length(trim(metric)) BETWEEN 1 AND 160',name='ck_process_measurements_metric_required'),sa.CheckConstraint("category IN ('measurement','defect','alarm','quality')",name='ck_process_measurements_category'),sa.CheckConstraint('revision >= 1',name='ck_process_measurements_revision'))
    op.create_index('ix_process_measurements_archived','process_measurements',['archived'])
    op.create_index('ix_process_measurements_category','process_measurements',['category'])
    op.create_index('ix_process_measurements_lot','process_measurements',['lot'])
    op.create_index('ix_process_measurements_metric','process_measurements',['metric'])
    op.create_index('ix_process_measurements_process','process_measurements',['process'])
    op.create_index('ix_process_measurements_sample_label','process_measurements',['sample_label'])
    op.create_index('ix_process_measurements_sampled_at','process_measurements',['sampled_at'])
    op.create_index('ix_process_measurements_subgroup','process_measurements',['subgroup'])
    op.create_index('ix_process_measurements_unit','process_measurements',['unit'])
    op.create_index('ix_process_measurements_value','process_measurements',['value'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
