from alembic import op
import sqlalchemy as sa
revision='tenant_0004'
down_revision='tenant_0003'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('racks',sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(120),nullable=False),sa.Column('site',sa.String(120),nullable=False),sa.Column('row_name',sa.String(80),nullable=True),sa.Column('rack_units',sa.Integer,nullable=False),sa.Column('power_capacity_kw',sa.Float,nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(name)) BETWEEN 1 AND 120',name='ck_racks_name_required'),sa.CheckConstraint('length(trim(site)) BETWEEN 1 AND 120',name='ck_racks_site_required'),sa.CheckConstraint('rack_units >= 1',name='ck_racks_rack_units_minimum'),sa.CheckConstraint('rack_units <= 1000',name='ck_racks_rack_units_maximum'),sa.CheckConstraint('power_capacity_kw >= 0',name='ck_racks_power_capacity_kw_minimum'),sa.CheckConstraint("status IN ('active','maintenance','retired')",name='ck_racks_status'),sa.CheckConstraint('revision >= 1',name='ck_racks_revision'))
    op.create_index('ix_racks_archived','racks',['archived'])
    op.create_index('ix_racks_name','racks',['name'])
    op.create_index('ix_racks_power_capacity_kw','racks',['power_capacity_kw'])
    op.create_index('ix_racks_rack_units','racks',['rack_units'])
    op.create_index('ix_racks_row_name','racks',['row_name'])
    op.create_index('ix_racks_site','racks',['site'])
    op.create_index('ix_racks_status','racks',['status'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
