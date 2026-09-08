from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='observability_events',label='Observability events',description='Canonical log, trace and metric events for reusable observability workspaces.',primary_field='event_id',fields=[
        FieldDefinition(key='event_id',label='Event ID',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='signal',label='Signal',kind='select',required=False,nullable=False,max_length=80,choices=['log', 'trace', 'metric'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='severity',label='Severity',kind='select',required=False,nullable=False,max_length=80,choices=['debug', 'info', 'warning', 'error', 'critical'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='timestamp',label='Timestamp',kind='datetime',required=True,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='duration_ms',label='Duration',kind='number',required=False,nullable=True,max_length=None,choices=[],minimum=0,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='trace_id',label='Trace ID',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='span_id',label='Span ID',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='parent_span_id',label='Parent span',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='operation',label='Operation',kind='text',required=False,nullable=True,max_length=200,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='message',label='Message',kind='textarea',required=False,nullable=True,max_length=30000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='attributes',label='Attributes',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['signal', 'severity'],sort_keys=['event_id', 'signal', 'severity', 'timestamp', 'duration_ms', 'trace_id', 'span_id', 'operation', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['event_id', 'signal', 'severity', 'timestamp', 'duration_ms', 'trace_id', 'span_id', 'operation', 'message', 'updated_at', 'revision'],capabilities=['observability', 'search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'timeline', 'dashboard'],visualizations=['observability', 'table', 'timeline', 'dashboard'])
