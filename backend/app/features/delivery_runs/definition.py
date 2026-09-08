from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='delivery_runs',label='Delivery runs',description='Canonical CI/CD pipeline and deployment execution records.',primary_field='run_id',fields=[
        FieldDefinition(key='run_id',label='Run ID',kind='text',required=True,nullable=False,max_length=120,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['queued', 'running', 'passed', 'failed', 'cancelled'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='environment',label='Environment',kind='select',required=False,nullable=False,max_length=80,choices=['development', 'test', 'staging', 'production'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='commit_sha',label='Commit',kind='text',required=False,nullable=True,max_length=80,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='branch',label='Branch',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='started_at',label='Started at',kind='datetime',required=True,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='completed_at',label='Completed at',kind='datetime',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='duration_minutes',label='Duration',kind='duration',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=None,step=None,unit='min',read_only=True),
        FieldDefinition(key='stages',label='Stages',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='artifacts',label='Artifacts',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='triggered_by',label='Triggered by',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['status', 'environment'],sort_keys=['run_id', 'status', 'environment', 'commit_sha', 'branch', 'started_at', 'completed_at', 'duration_minutes', 'triggered_by', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['run_id', 'status', 'environment', 'commit_sha', 'branch', 'started_at', 'completed_at', 'duration_minutes', 'triggered_by', 'updated_at', 'revision'],capabilities=['pipeline', 'search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'timeline', 'dashboard'],visualizations=['pipeline', 'table', 'timeline', 'dashboard'])
