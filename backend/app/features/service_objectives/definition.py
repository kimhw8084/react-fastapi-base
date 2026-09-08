from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='service_objectives',label='Service objectives',description='Canonical SLO/error-budget records with server-owned burn and remaining-budget calculations.',primary_field='name',fields=[
        FieldDefinition(key='name',label='SLO name',kind='text',required=True,nullable=False,max_length=200,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='window_days',label='Window',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=1,maximum=365,step=None,unit=None,read_only=False),
        FieldDefinition(key='target_percent',label='Target',kind='percent',required=False,nullable=False,max_length=None,choices=[],minimum=0.001,maximum=100,step=None,unit='%',read_only=False),
        FieldDefinition(key='current_percent',label='Current',kind='percent',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=100,step=None,unit='%',read_only=False),
        FieldDefinition(key='error_budget_remaining',label='Budget remaining',kind='percent',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=100,step=None,unit='%',read_only=True),
        FieldDefinition(key='burn_rate',label='Burn rate',kind='number',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=None,step=None,unit=None,read_only=True),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['healthy', 'warning', 'exhausted'],minimum=None,maximum=None,step=None,unit=None,read_only=True),
        FieldDefinition(key='notes',label='Notes',kind='markdown',required=False,nullable=True,max_length=30000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['status'],sort_keys=['name', 'window_days', 'target_percent', 'current_percent', 'error_budget_remaining', 'burn_rate', 'status', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['name', 'window_days', 'target_percent', 'current_percent', 'error_budget_remaining', 'burn_rate', 'status', 'updated_at', 'revision'],capabilities=['slo', 'search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'dashboard'],visualizations=['slo', 'table', 'dashboard'])
