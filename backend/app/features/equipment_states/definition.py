from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='equipment_states',label='Equipment states',description='Canonical equipment/module state intervals for utilization, downtime and reason analysis.',primary_field='label',fields=[
        FieldDefinition(key='label',label='State interval',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='state',label='State',kind='select',required=True,nullable=False,max_length=80,choices=['production', 'standby', 'engineering', 'scheduled_down', 'unscheduled_down'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='module',label='Module / chamber',kind='text',required=False,nullable=True,max_length=120,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='started_at',label='Started at',kind='datetime',required=True,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='ended_at',label='Ended at',kind='datetime',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='duration_minutes',label='Duration',kind='duration',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=None,step=None,unit='min',read_only=True),
        FieldDefinition(key='reason',label='Reason',kind='textarea',required=False,nullable=True,max_length=10000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='alarm_code',label='Alarm code',kind='text',required=False,nullable=True,max_length=80,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='context',label='Context',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['state'],sort_keys=['label', 'state', 'module', 'started_at', 'ended_at', 'duration_minutes', 'alarm_code', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['label', 'state', 'module', 'started_at', 'ended_at', 'duration_minutes', 'alarm_code', 'updated_at', 'revision'],capabilities=['state_timeline', 'search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'timeline', 'dashboard'],visualizations=['state_timeline', 'table', 'timeline', 'dashboard'])
