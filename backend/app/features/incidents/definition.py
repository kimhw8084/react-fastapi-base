from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='incidents',label='Incidents',description='Canonical incident command records with timeline, impact, ownership and action context.',primary_field='title',fields=[
        FieldDefinition(key='incident_number',label='Incident number',kind='text',required=True,nullable=False,max_length=80,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='title',label='Title',kind='text',required=True,nullable=False,max_length=240,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['investigating', 'identified', 'monitoring', 'resolved', 'closed'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='severity',label='Severity',kind='select',required=False,nullable=False,max_length=80,choices=['sev_1', 'sev_2', 'sev_3', 'sev_4'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='started_at',label='Started at',kind='datetime',required=True,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='resolved_at',label='Resolved at',kind='datetime',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='duration_minutes',label='Duration',kind='duration',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=None,step=None,unit='min',read_only=True),
        FieldDefinition(key='commander',label='Commander',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='impact',label='Impact',kind='markdown',required=False,nullable=True,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='timeline',label='Timeline',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='actions',label='Actions',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['status', 'severity'],sort_keys=['incident_number', 'title', 'status', 'severity', 'started_at', 'resolved_at', 'duration_minutes', 'commander', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['incident_number', 'title', 'status', 'severity', 'started_at', 'resolved_at', 'duration_minutes', 'commander', 'updated_at', 'revision'],capabilities=['incident_command', 'search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'board', 'timeline', 'dashboard'],visualizations=['incident_command', 'table', 'board', 'timeline', 'dashboard'])
