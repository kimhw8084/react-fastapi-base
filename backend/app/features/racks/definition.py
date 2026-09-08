from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='racks',label='Racks',description='Canonical physical rack records for reusable estate and placement workspaces.',primary_field='name',fields=[
        FieldDefinition(key='name',label='Rack name',kind='text',required=True,nullable=False,max_length=120,choices=[],minimum=None,maximum=None,step=None),
        FieldDefinition(key='site',label='Site',kind='text',required=True,nullable=False,max_length=120,choices=[],minimum=None,maximum=None,step=None),
        FieldDefinition(key='row_name',label='Row',kind='text',required=False,nullable=True,max_length=80,choices=[],minimum=None,maximum=None,step=None),
        FieldDefinition(key='rack_units',label='Rack units',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=1,maximum=1000,step=None),
        FieldDefinition(key='power_capacity_kw',label='Power capacity kW',kind='number',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=None,step=0.1),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['active', 'maintenance', 'retired'],minimum=None,maximum=None,step=None)
    ],filter_keys=['status'],sort_keys=['name', 'site', 'row_name', 'rack_units', 'power_capacity_kw', 'status', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['name', 'site', 'row_name', 'rack_units', 'power_capacity_kw', 'status', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'dashboard', 'graph', 'rack'],visualizations=['table', 'dashboard', 'graph', 'rack'])
