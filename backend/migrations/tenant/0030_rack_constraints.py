from alembic import op
import sqlalchemy as sa

revision='tenant_0030'
down_revision='tenant_0029'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('racks',sa.Column('pdu_a_capacity_kw',sa.Float(),nullable=True))
    op.add_column('racks',sa.Column('pdu_b_capacity_kw',sa.Float(),nullable=True))
    op.add_column('racks',sa.Column('weight_capacity_kg',sa.Float(),nullable=True))
    op.add_column('racks',sa.Column('thermal_capacity_kw',sa.Float(),nullable=True))
    op.add_column('racks',sa.Column('reserved_units',sa.Integer(),nullable=False,server_default='0'))
    op.add_column('racks',sa.Column('reserved_power_kw',sa.Float(),nullable=False,server_default='0'))

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
