from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='equipment',label='Equipment',description='Canonical equipment records placed into physical layouts without copying identity data.',primary_field='name',fields=[
        FieldDefinition(key='name',label='Equipment name',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None),
        FieldDefinition(key='kind',label='Type',kind='select',required=False,nullable=False,max_length=80,choices=['server', 'switch', 'storage', 'appliance', 'other'],minimum=None,maximum=None,step=None),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['active', 'maintenance', 'offline', 'retired'],minimum=None,maximum=None,step=None),
        FieldDefinition(key='serial',label='Serial',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None),
        FieldDefinition(key='power_kw',label='Power kW',kind='number',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=None,step=0.1),
        FieldDefinition(key='notes',label='Notes',kind='textarea',required=False,nullable=True,max_length=10000,choices=[],minimum=None,maximum=None,step=None)
    ],filter_keys=['kind', 'status'],sort_keys=['name', 'kind', 'status', 'serial', 'power_kw', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['name', 'kind', 'status', 'serial', 'power_kw', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'board', 'dashboard', 'graph'],visualizations=['table', 'board', 'dashboard', 'graph'])
