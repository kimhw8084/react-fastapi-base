from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='research',label='Research',description='Canonical engineering research records for hypotheses, experiments, evidence, analysis and recommendations.',primary_field='title',fields=[
        FieldDefinition(key='title',label='Title',kind='text',required=True,nullable=False,max_length=200,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['question', 'researching', 'experimenting', 'analyzing', 'review', 'complete'],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='phase',label='Phase',kind='select',required=False,nullable=False,max_length=80,choices=['discovery', 'hypothesis', 'experiment', 'analysis', 'conclusion'],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='question',label='Research question',kind='textarea',required=True,nullable=False,max_length=20000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='hypothesis',label='Hypothesis',kind='markdown',required=False,nullable=True,max_length=60000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='methodology',label='Methodology',kind='markdown',required=False,nullable=True,max_length=60000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='experiments',label='Experiments',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='evidence',label='Evidence',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='analysis',label='Analysis',kind='markdown',required=False,nullable=True,max_length=80000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='findings',label='Findings',kind='markdown',required=False,nullable=True,max_length=80000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='conclusion',label='Conclusion',kind='markdown',required=False,nullable=True,max_length=60000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='recommendation',label='Recommendation',kind='markdown',required=False,nullable=True,max_length=60000,choices=[],minimum=None,maximum=None,step=None,unit=None)
    ],filter_keys=['status', 'phase'],sort_keys=['title', 'status', 'phase', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['title', 'status', 'phase', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'board', 'timeline', 'dashboard', 'graph'],visualizations=['research', 'table', 'board', 'timeline', 'dashboard', 'graph'])
