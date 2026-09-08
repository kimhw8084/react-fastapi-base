from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='process_recipes',label='Process recipes',description='Canonical versioned process recipe records with structured parameters, limits and approval context.',primary_field='name',fields=[
        FieldDefinition(key='name',label='Recipe name',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='version_name',label='Version',kind='text',required=True,nullable=False,max_length=80,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='process',label='Process',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['draft', 'qualified', 'released', 'deprecated'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='parameters',label='Parameters',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='limits',label='Limits',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='approved_by',label='Approved by',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='approved_at',label='Approved at',kind='datetime',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='notes',label='Notes',kind='markdown',required=False,nullable=True,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['status'],sort_keys=['name', 'version_name', 'process', 'status', 'approved_by', 'approved_at', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['name', 'version_name', 'process', 'status', 'approved_by', 'approved_at', 'updated_at', 'revision'],capabilities=['recipe', 'search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'dashboard'],visualizations=['recipe', 'table', 'dashboard'])
