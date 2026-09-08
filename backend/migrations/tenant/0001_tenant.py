from alembic import op
import sqlalchemy as sa
revision = 'tenant_0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('work_items',
      sa.Column('id',sa.String(36),primary_key=True),sa.Column('title',sa.String(160),nullable=False),
      sa.Column('description',sa.Text(),nullable=False),sa.Column('status',sa.String(20),nullable=False),
      sa.Column('priority',sa.String(20),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),
      sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),
      sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
      sa.CheckConstraint("status IN ('open','in_progress','done')",name='ck_work_item_status'),
      sa.CheckConstraint("priority IN ('low','normal','high')",name='ck_work_item_priority'),
      sa.CheckConstraint('revision >= 1',name='ck_work_item_revision'),
      sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 160',name='ck_work_item_title'))
    for field in ('title','status','priority','archived'):
        op.create_index(f'ix_work_items_{field}','work_items',[field])
    op.create_table('audit_events',
      sa.Column('id',sa.String(36),primary_key=True),sa.Column('actor',sa.String(200),nullable=False),
      sa.Column('workspace',sa.String(40),nullable=False),sa.Column('entity_id',sa.String(36),nullable=False),
      sa.Column('action',sa.String(40),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),
      sa.Column('before',sa.JSON()),sa.Column('after',sa.JSON()),sa.Column('request_id',sa.String(36),nullable=False),
      sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
      sa.UniqueConstraint('workspace','entity_id','revision',name='uq_audit_entity_revision'))
    for field in ('actor','workspace','entity_id'):
        op.create_index(f'ix_audit_events_{field}','audit_events',[field])
    op.create_table('saved_views',
      sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace',sa.String(40),nullable=False),
      sa.Column('owner',sa.String(200),nullable=False),sa.Column('scope',sa.String(20),nullable=False),
      sa.Column('name',sa.String(120),nullable=False),sa.Column('definition',sa.JSON(),nullable=False),
      sa.Column('revision',sa.Integer(),nullable=False),sa.Column('schema_version',sa.Integer(),nullable=False),
      sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
      sa.CheckConstraint("scope IN ('personal','team')",name='ck_view_scope'))
    op.create_index('ix_saved_views_workspace','saved_views',['workspace'])
    op.create_table('idempotency_entries',
      sa.Column('owner',sa.String(200),primary_key=True),sa.Column('key',sa.String(128),primary_key=True),
      sa.Column('fingerprint',sa.String(64),nullable=False),sa.Column('response',sa.JSON(),nullable=False),
      sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('attachments',
      sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace',sa.String(40),nullable=False),
      sa.Column('entity_id',sa.String(36),nullable=False),sa.Column('filename',sa.String(180),nullable=False),
      sa.Column('content_type',sa.String(100),nullable=False),sa.Column('size',sa.Integer(),nullable=False),
      sa.Column('sha256',sa.String(64),nullable=False),sa.Column('content',sa.LargeBinary(),nullable=False),
      sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_attachments_entity_id','attachments',['entity_id'])
    # Application writers cannot change audit history through the common engine.
    op.execute("CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_events BEGIN SELECT RAISE(ABORT, 'Audit history is append-only'); END")
    op.execute("CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_events BEGIN SELECT RAISE(ABORT, 'Audit history is append-only'); END")

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
