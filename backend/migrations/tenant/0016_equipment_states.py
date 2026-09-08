from alembic import op
import sqlalchemy as sa
revision='tenant_0016'
down_revision='tenant_0015'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('equipment_states',sa.Column('id',sa.String(36),primary_key=True),sa.Column('label',sa.String(160),nullable=False),sa.Column('state',sa.String(80),nullable=False),sa.Column('module',sa.String(120),nullable=True),sa.Column('started_at',sa.DateTime(timezone=True),nullable=False),sa.Column('ended_at',sa.DateTime(timezone=True),nullable=True),sa.Column('duration_minutes',sa.Float,nullable=False),sa.Column('reason',sa.String(10000),nullable=True),sa.Column('alarm_code',sa.String(80),nullable=True),sa.Column('context',sa.JSON,nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('archived',sa.Boolean(),nullable=False),sa.Column('created_by',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.CheckConstraint('length(trim(label)) BETWEEN 1 AND 160',name='ck_equipment_states_label_required'),sa.CheckConstraint("state IN ('production','standby','engineering','scheduled_down','unscheduled_down')",name='ck_equipment_states_state'),sa.CheckConstraint('length(trim(state)) BETWEEN 1 AND 80',name='ck_equipment_states_state_required'),sa.CheckConstraint('duration_minutes >= 0',name='ck_equipment_states_duration_minutes_minimum'),sa.CheckConstraint('revision >= 1',name='ck_equipment_states_revision'))
    op.create_index('ix_equipment_states_alarm_code','equipment_states',['alarm_code'])
    op.create_index('ix_equipment_states_archived','equipment_states',['archived'])
    op.create_index('ix_equipment_states_duration_minutes','equipment_states',['duration_minutes'])
    op.create_index('ix_equipment_states_ended_at','equipment_states',['ended_at'])
    op.create_index('ix_equipment_states_label','equipment_states',['label'])
    op.create_index('ix_equipment_states_module','equipment_states',['module'])
    op.create_index('ix_equipment_states_started_at','equipment_states',['started_at'])
    op.create_index('ix_equipment_states_state','equipment_states',['state'])
def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')
