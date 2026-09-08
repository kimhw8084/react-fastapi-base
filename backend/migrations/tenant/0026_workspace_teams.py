from alembic import op
import sqlalchemy as sa

revision = 'tenant_0026'
down_revision = 'tenant_0025'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('workspace_teams',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('name',sa.String(120),nullable=False),
        sa.Column('slug',sa.String(80),nullable=False,unique=True),sa.Column('owner',sa.String(200),nullable=False),
        sa.Column('is_default',sa.Boolean(),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.CheckConstraint('revision >= 1',name='ck_workspace_teams_revision'))
    op.create_index('ix_workspace_teams_is_default','workspace_teams',['is_default'])
    op.create_table('workspace_team_members',
        sa.Column('team_id',sa.String(36),nullable=False),sa.Column('user_id',sa.String(200),nullable=False),
        sa.Column('role',sa.String(20),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.PrimaryKeyConstraint('team_id','user_id'),sa.ForeignKeyConstraint(['team_id'],['workspace_teams.id'],ondelete='CASCADE'),
        sa.CheckConstraint("role IN ('member','manager')",name='ck_workspace_team_members_role'))
    with op.batch_alter_table('saved_views') as batch:
        batch.add_column(sa.Column('team_id',sa.String(36),nullable=True))
        batch.create_index('ix_saved_views_team_id',['team_id'])

def downgrade():
    raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
