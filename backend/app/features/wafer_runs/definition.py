from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='wafer_runs',label='Wafer runs',description='Canonical wafer result records with tested die/bin summaries and traceable process context.',primary_field='wafer_id',fields=[
        FieldDefinition(key='wafer_id',label='Wafer ID',kind='text',required=True,nullable=False,max_length=120,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='lot_id',label='Lot ID',kind='text',required=True,nullable=False,max_length=120,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='process_step',label='Process step',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['queued', 'processing', 'complete', 'hold', 'scrapped'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='die_rows',label='Die rows',kind='integer',required=True,nullable=False,max_length=None,choices=[],minimum=1,maximum=100,step=None,unit=None,read_only=False),
        FieldDefinition(key='die_cols',label='Die columns',kind='integer',required=True,nullable=False,max_length=None,choices=[],minimum=1,maximum=100,step=None,unit=None,read_only=False),
        FieldDefinition(key='bin_map',label='Bin map',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='total_die',label='Tested die',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=True),
        FieldDefinition(key='good_die',label='Good die',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=True),
        FieldDefinition(key='defect_count',label='Defects',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=True),
        FieldDefinition(key='yield_percent',label='Yield',kind='percent',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=100,step=None,unit='%',read_only=True),
        FieldDefinition(key='completed_at',label='Completed at',kind='datetime',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='notes',label='Notes',kind='markdown',required=False,nullable=True,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['status'],sort_keys=['wafer_id', 'lot_id', 'process_step', 'status', 'total_die', 'good_die', 'defect_count', 'yield_percent', 'completed_at', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['wafer_id', 'lot_id', 'process_step', 'status', 'total_die', 'good_die', 'defect_count', 'yield_percent', 'completed_at', 'updated_at', 'revision'],capabilities=['wafer', 'search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'dashboard', 'timeline'],visualizations=['wafer', 'table', 'dashboard', 'timeline'])
