from alembic import op
import sqlalchemy as sa

revision='tenant_0031'
down_revision='tenant_0030'
branch_labels=None
depends_on=None

def upgrade():
    with op.batch_alter_table('saved_views') as batch:
        batch.add_column(sa.Column('is_favorite',sa.Boolean(),nullable=False,server_default=sa.false()))
        batch.add_column(sa.Column('is_default',sa.Boolean(),nullable=False,server_default=sa.false()))
        batch.create_index('ix_saved_views_is_favorite',['is_favorite'])
        batch.create_index('ix_saved_views_is_default',['is_default'])

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
