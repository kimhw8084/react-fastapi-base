from alembic import op
import sqlalchemy as sa

revision = 'tenant_0025'
down_revision = 'tenant_0024'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('notifications') as batch:
        batch.add_column(sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True))
        batch.create_index('ix_notifications_dismissed_at', ['dismissed_at'])


def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
