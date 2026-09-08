from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='plan_tasks',label='Planning',description='Canonical plan tasks shared by table, board, Gantt, calendar, timeline and dependency projections.',primary_field='title',fields=[
        FieldDefinition(key='title',label='Title',kind='text',required=True,nullable=False,max_length=200,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['planned', 'ready', 'in_progress', 'blocked', 'done', 'cancelled'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='start_date',label='Start date',kind='date',required=True,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='end_date',label='End date',kind='date',required=True,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='baseline_start',label='Baseline start',kind='date',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='baseline_end',label='Baseline end',kind='date',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='progress',label='Progress',kind='percent',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=100,step=None,unit='%',read_only=False),
        FieldDefinition(key='milestone',label='Milestone',kind='boolean',required=False,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='owner',label='Owner',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='duration_days',label='Duration days',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=1,maximum=3650,step=None,unit=None,read_only=True),
        FieldDefinition(key='notes',label='Notes',kind='textarea',required=False,nullable=True,max_length=20000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['status', 'milestone'],sort_keys=['title', 'status', 'start_date', 'end_date', 'baseline_start', 'baseline_end', 'progress', 'milestone', 'owner', 'duration_days', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['title', 'status', 'start_date', 'end_date', 'progress', 'milestone', 'owner', 'duration_days', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'board', 'gantt', 'calendar', 'timeline', 'dashboard', 'graph'],visualizations=['planning','table','board','gantt','calendar','timeline','dashboard','graph'])
