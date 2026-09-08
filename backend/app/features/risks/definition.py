from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='risks',label='Risk analysis',description='Canonical risk and FMEA-style records with scoring, mitigation and prevention context.',primary_field='title',fields=[
        FieldDefinition(key='title',label='Title',kind='text',required=True,nullable=False,max_length=200,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['identified', 'assessing', 'mitigating', 'monitoring', 'closed'],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='category',label='Category',kind='select',required=False,nullable=False,max_length=80,choices=['design', 'process', 'hardware', 'software', 'network', 'human', 'environment'],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='severity',label='Severity',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=1,maximum=10,step=None,unit=None),
        FieldDefinition(key='occurrence',label='Occurrence',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=1,maximum=10,step=None,unit=None),
        FieldDefinition(key='detection',label='Detection',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=1,maximum=10,step=None,unit=None),
        FieldDefinition(key='rpn',label='RPN',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=1,maximum=1000,step=None,unit=None,read_only=True),
        FieldDefinition(key='residual_severity',label='Residual severity',kind='integer',required=False,nullable=True,max_length=None,choices=[],minimum=1,maximum=10,step=None,unit=None),
        FieldDefinition(key='residual_occurrence',label='Residual occurrence',kind='integer',required=False,nullable=True,max_length=None,choices=[],minimum=1,maximum=10,step=None,unit=None),
        FieldDefinition(key='residual_detection',label='Residual detection',kind='integer',required=False,nullable=True,max_length=None,choices=[],minimum=1,maximum=10,step=None,unit=None),
        FieldDefinition(key='residual_rpn',label='Residual RPN',kind='integer',required=False,nullable=True,max_length=None,choices=[],minimum=1,maximum=1000,step=None,unit=None,read_only=True),
        FieldDefinition(key='effect',label='Effect',kind='textarea',required=False,nullable=True,max_length=20000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='causes',label='Causes',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='mitigations',label='Mitigations',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None),
        FieldDefinition(key='prevention',label='Prevention',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None)
    ],filter_keys=['status', 'category'],sort_keys=['title', 'status', 'category', 'severity', 'occurrence', 'detection', 'rpn', 'residual_severity', 'residual_occurrence', 'residual_detection', 'residual_rpn', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['title', 'status', 'category', 'severity', 'occurrence', 'detection', 'rpn', 'residual_rpn', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'dashboard', 'timeline', 'graph'],visualizations=['risk', 'table', 'dashboard', 'timeline', 'graph'])
