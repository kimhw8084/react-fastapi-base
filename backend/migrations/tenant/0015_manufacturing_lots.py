from alembic import op
import sqlalchemy as sa
revision='tenant_0015'
down_revision='tenant_0014'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('manufacturing_lots',sa.Column('id',sa.String(36),primary_key=True),sa.Column('lot_id',sa.String(120),nullable=False),sa.Column('product',sa.String(160),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('current_step',sa.String(160),nullable=True),sa.Column('priority',sa.String(80),nullable=False),sa.Column('quantity',sa.Integer,nullable=False),sa.Column('started_at',sa.DateTime(timezone=True),nullable=True),sa.Column('target_complete',sa.DateTime(timezone=True),nullable=True),sa.Column('route',sa.JSON,nullable=False),sa.Column('hold_reason',sa.String(10000),nullable=True),sa.Column('owner',sa.String(160),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(lot_id)) BETWEEN 1 AND 120',name='ck_manufacturing_lots_lot_id_required'),sa.CheckConstraint('length(trim(product)) BETWEEN 1 AND 160',name='ck_manufacturing_lots_product_required'),sa.CheckConstraint("status IN ('queued','running','hold','complete','scrapped')",name='ck_manufacturing_lots_status'),sa.CheckConstraint("priority IN ('low','normal','high','hot')",name='ck_manufacturing_lots_priority'),sa.CheckConstraint('quantity >= 0',name='ck_manufacturing_lots_quantity_minimum'),sa.CheckConstraint('revision >= 1',name='ck_manufacturing_lots_revision'))
    op.create_index('ix_manufacturing_lots_archived','manufacturing_lots',['archived'])
    op.create_index('ix_manufacturing_lots_current_step','manufacturing_lots',['current_step'])
    op.create_index('ix_manufacturing_lots_lot_id','manufacturing_lots',['lot_id'])
    op.create_index('ix_manufacturing_lots_owner','manufacturing_lots',['owner'])
    op.create_index('ix_manufacturing_lots_priority','manufacturing_lots',['priority'])
    op.create_index('ix_manufacturing_lots_product','manufacturing_lots',['product'])
    op.create_index('ix_manufacturing_lots_quantity','manufacturing_lots',['quantity'])
    op.create_index('ix_manufacturing_lots_started_at','manufacturing_lots',['started_at'])
    op.create_index('ix_manufacturing_lots_status','manufacturing_lots',['status'])
    op.create_index('ix_manufacturing_lots_target_complete','manufacturing_lots',['target_complete'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
