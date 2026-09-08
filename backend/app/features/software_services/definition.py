from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='software_services',label='Software services',description='Canonical software/service registry records used by delivery, observability, incidents and SLO workspaces.',primary_field='name',fields=[
        FieldDefinition(key='name',label='Service name',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['healthy', 'degraded', 'maintenance', 'retired'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='tier',label='Tier',kind='select',required=False,nullable=False,max_length=80,choices=['tier_0', 'tier_1', 'tier_2', 'tier_3'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='owner',label='Owner',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='repository',label='Repository',kind='url',required=False,nullable=True,max_length=500,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='runtime',label='Runtime',kind='text',required=False,nullable=True,max_length=120,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='environment',label='Environment',kind='select',required=False,nullable=False,max_length=80,choices=['development', 'test', 'staging', 'production'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='config',label='Runtime config',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='description',label='Description',kind='markdown',required=False,nullable=True,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['status', 'tier', 'environment'],sort_keys=['name', 'status', 'tier', 'owner', 'repository', 'runtime', 'environment', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['name', 'status', 'tier', 'owner', 'repository', 'runtime', 'environment', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'dashboard', 'graph'],visualizations=['table', 'dashboard', 'graph'])
