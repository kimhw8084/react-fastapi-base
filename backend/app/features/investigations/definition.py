from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='investigations',label='Investigations',description='Canonical investigation records covering problem definition, evidence, hypotheses, causes, actions and conclusions.',primary_field='title',fields=[
        FieldDefinition(key='title',label='Title',kind='text',required=True,nullable=False,max_length=200,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['open', 'investigating', 'validated', 'resolved', 'closed'],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='priority',label='Priority',kind='select',required=False,nullable=False,max_length=80,choices=['low', 'medium', 'high', 'critical'],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='problem',label='Problem definition',kind='textarea',required=True,nullable=False,max_length=20000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='evidence',label='Evidence',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='hypotheses',label='Hypotheses',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='causes',label='Causes',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='actions',label='Actions',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='findings',label='Findings',kind='markdown',required=False,nullable=True,max_length=60000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='conclusion',label='Conclusion',kind='markdown',required=False,nullable=True,max_length=60000,choices=[],minimum=None,maximum=None,step=None,unit=None)
    ],filter_keys=['status', 'priority'],sort_keys=['title', 'status', 'priority', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['title', 'status', 'priority', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'board', 'timeline', 'dashboard', 'graph'],visualizations=['investigation', 'table', 'board', 'timeline', 'dashboard', 'graph'])
