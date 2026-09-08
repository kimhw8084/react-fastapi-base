from alembic import op
import sqlalchemy as sa
revision='tenant_0014'
down_revision='tenant_0013'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('wafer_runs',sa.Column('id',sa.String(36),primary_key=True),sa.Column('wafer_id',sa.String(120),nullable=False),sa.Column('lot_id',sa.String(120),nullable=False),sa.Column('process_step',sa.String(160),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('die_rows',sa.Integer,nullable=False),sa.Column('die_cols',sa.Integer,nullable=False),sa.Column('bin_map',sa.JSON,nullable=False),sa.Column('total_die',sa.Integer,nullable=False),sa.Column('good_die',sa.Integer,nullable=False),sa.Column('defect_count',sa.Integer,nullable=False),sa.Column('yield_percent',sa.Float,nullable=False),sa.Column('completed_at',sa.DateTime(timezone=True),nullable=True),sa.Column('notes',sa.String(50000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(wafer_id)) BETWEEN 1 AND 120',name='ck_wafer_runs_wafer_id_required'),sa.CheckConstraint('length(trim(lot_id)) BETWEEN 1 AND 120',name='ck_wafer_runs_lot_id_required'),sa.CheckConstraint('length(trim(process_step)) BETWEEN 1 AND 160',name='ck_wafer_runs_process_step_required'),sa.CheckConstraint("status IN ('queued','processing','complete','hold','scrapped')",name='ck_wafer_runs_status'),sa.CheckConstraint('die_rows >= 1',name='ck_wafer_runs_die_rows_minimum'),sa.CheckConstraint('die_rows <= 100',name='ck_wafer_runs_die_rows_maximum'),sa.CheckConstraint('die_cols >= 1',name='ck_wafer_runs_die_cols_minimum'),sa.CheckConstraint('die_cols <= 100',name='ck_wafer_runs_die_cols_maximum'),sa.CheckConstraint('yield_percent >= 0',name='ck_wafer_runs_yield_percent_minimum'),sa.CheckConstraint('yield_percent <= 100',name='ck_wafer_runs_yield_percent_maximum'),sa.CheckConstraint('revision >= 1',name='ck_wafer_runs_revision'))
    op.create_index('ix_wafer_runs_archived','wafer_runs',['archived'])
    op.create_index('ix_wafer_runs_completed_at','wafer_runs',['completed_at'])
    op.create_index('ix_wafer_runs_defect_count','wafer_runs',['defect_count'])
    op.create_index('ix_wafer_runs_good_die','wafer_runs',['good_die'])
    op.create_index('ix_wafer_runs_lot_id','wafer_runs',['lot_id'])
    op.create_index('ix_wafer_runs_process_step','wafer_runs',['process_step'])
    op.create_index('ix_wafer_runs_status','wafer_runs',['status'])
    op.create_index('ix_wafer_runs_total_die','wafer_runs',['total_die'])
    op.create_index('ix_wafer_runs_wafer_id','wafer_runs',['wafer_id'])
    op.create_index('ix_wafer_runs_yield_percent','wafer_runs',['yield_percent'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
