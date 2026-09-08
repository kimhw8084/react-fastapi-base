from alembic import op
import sqlalchemy as sa
revision='tenant_0021'
down_revision='tenant_0020'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('incidents',sa.Column('id',sa.String(36),primary_key=True),sa.Column('incident_number',sa.String(80),nullable=False),sa.Column('title',sa.String(240),nullable=False),sa.Column('status',sa.String(80),nullable=False),sa.Column('severity',sa.String(80),nullable=False),sa.Column('started_at',sa.DateTime(timezone=True),nullable=False),sa.Column('resolved_at',sa.DateTime(timezone=True),nullable=True),sa.Column('duration_minutes',sa.Float,nullable=False),sa.Column('commander',sa.String(160),nullable=True),sa.Column('impact',sa.String(50000),nullable=True),sa.Column('timeline',sa.JSON,nullable=False),sa.Column('actions',sa.JSON,nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(incident_number)) BETWEEN 1 AND 80',name='ck_incidents_incident_number_required'),sa.CheckConstraint('length(trim(title)) BETWEEN 1 AND 240',name='ck_incidents_title_required'),sa.CheckConstraint("status IN ('investigating','identified','monitoring','resolved','closed')",name='ck_incidents_status'),sa.CheckConstraint("severity IN ('sev_1','sev_2','sev_3','sev_4')",name='ck_incidents_severity'),sa.CheckConstraint('duration_minutes >= 0',name='ck_incidents_duration_minutes_minimum'),sa.CheckConstraint('revision >= 1',name='ck_incidents_revision'))
    op.create_index('ix_incidents_archived','incidents',['archived'])
    op.create_index('ix_incidents_commander','incidents',['commander'])
    op.create_index('ix_incidents_duration_minutes','incidents',['duration_minutes'])
    op.create_index('ix_incidents_incident_number','incidents',['incident_number'])
    op.create_index('ix_incidents_resolved_at','incidents',['resolved_at'])
    op.create_index('ix_incidents_severity','incidents',['severity'])
    op.create_index('ix_incidents_started_at','incidents',['started_at'])
    op.create_index('ix_incidents_status','incidents',['status'])
    op.create_index('ix_incidents_title','incidents',['title'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
