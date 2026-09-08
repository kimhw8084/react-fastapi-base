from alembic import op
import sqlalchemy as sa

revision='tenant_0028'
down_revision='tenant_0027'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('attachments',sa.Column('object_key',sa.String(240),nullable=True))
    # SQLite cannot ALTER a unique constraint in place; a unique index gives
    # the same invariant and remains compatible with existing rows.
    op.create_index('uq_attachments_object_key','attachments',['object_key'],unique=True)
    op.create_table('record_comments',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('workspace',sa.String(80),nullable=False),
        sa.Column('entity',sa.String(80),nullable=False),
        sa.Column('entity_id',sa.String(64),nullable=False),
        sa.Column('author',sa.String(200),nullable=False),
        sa.Column('body',sa.Text(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    for column in ('workspace','entity','entity_id','author','created_at'):
        op.create_index(f'ix_record_comments_{column}','record_comments',[column])

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
