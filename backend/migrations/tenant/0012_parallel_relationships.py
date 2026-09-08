from alembic import op
revision='tenant_0012'
down_revision='tenant_0011'
branch_labels=None
depends_on=None

def upgrade():
    # Parallel physical/logical edges are valid when their relationship definition
    # opts in. Application-level guards enforce definition/cardinality/port rules.
    with op.batch_alter_table('entity_relationships',recreate='always') as batch:
        batch.drop_constraint('uq_entity_relationship_pair',type_='unique')

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
