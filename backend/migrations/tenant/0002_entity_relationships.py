from alembic import op
import sqlalchemy as sa
revision='tenant_0002'
down_revision='tenant_0001'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('entity_relationships',
      sa.Column('id',sa.String(36),primary_key=True),
      sa.Column('definition_key',sa.String(60),nullable=False),
      sa.Column('source_entity',sa.String(40),nullable=False),
      sa.Column('source_id',sa.String(64),nullable=False),
      sa.Column('target_entity',sa.String(40),nullable=False),
      sa.Column('target_id',sa.String(64),nullable=False),
      sa.Column('metadata',sa.JSON(),nullable=False),
      sa.Column('revision',sa.Integer(),nullable=False),
      sa.Column('archived',sa.Boolean(),nullable=False),
      sa.Column('created_by',sa.String(200),nullable=False),
      sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
      sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
      sa.UniqueConstraint('definition_key','source_id','target_id',name='uq_entity_relationship_pair'),
      sa.CheckConstraint('revision >= 1',name='ck_entity_relationship_revision'))
    for field in ('definition_key','source_entity','source_id','target_entity','target_id','archived'):
        op.create_index(f'ix_entity_relationships_{field}','entity_relationships',[field])

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
