from alembic import op
import sqlalchemy as sa

revision = 'tenant_0024'
down_revision = 'tenant_0023'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('durable_jobs') as batch:
        batch.add_column(sa.Column('fence_token', sa.String(36), nullable=True))
        batch.drop_constraint('ck_durable_jobs_status', type_='check')
        batch.create_check_constraint(
            'ck_durable_jobs_status',
            "status IN ('queued','running','retrying','succeeded','failed','cancelled')",
        )


def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
