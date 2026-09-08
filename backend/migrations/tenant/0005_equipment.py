from alembic import op
import sqlalchemy as sa
revision='tenant_0005'
down_revision='tenant_0004'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('equipment',sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(160),nullable=False),sa.Column('kind',sa.String(80),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('serial',sa.String(160),nullable=True),sa.Column('power_kw',sa.Float,nullable=False),sa.Column('notes',sa.String(10000),nullable=True),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(name)) BETWEEN 1 AND 160',name='ck_equipment_name_required'),sa.CheckConstraint("kind IN ('server','switch','storage','appliance','other')",name='ck_equipment_kind'),sa.CheckConstraint("status IN ('active','maintenance','offline','retired')",name='ck_equipment_status'),sa.CheckConstraint('power_kw >= 0',name='ck_equipment_power_kw_minimum'),sa.CheckConstraint('revision >= 1',name='ck_equipment_revision'))
    op.create_index('ix_equipment_archived','equipment',['archived'])
    op.create_index('ix_equipment_kind','equipment',['kind'])
    op.create_index('ix_equipment_name','equipment',['name'])
    op.create_index('ix_equipment_power_kw','equipment',['power_kw'])
    op.create_index('ix_equipment_serial','equipment',['serial'])
    op.create_index('ix_equipment_status','equipment',['status'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
