from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='process_measurements',label='Process measurements',description='Canonical engineering measurement samples for SPC, capability, trend and trace analysis.',primary_field='sample_label',fields=[
        FieldDefinition(key='sample_label',label='Sample',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='process',label='Process',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='metric',label='Metric',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='value',label='Value',kind='scientific',required=True,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='unit',label='Unit',kind='text',required=False,nullable=True,max_length=32,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='sampled_at',label='Sampled at',kind='datetime',required=True,nullable=False,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='subgroup',label='Subgroup',kind='text',required=False,nullable=True,max_length=80,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='target',label='Target',kind='number',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='lower_spec',label='Lower spec',kind='number',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='upper_spec',label='Upper spec',kind='number',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='lot',label='Lot / batch',kind='text',required=False,nullable=True,max_length=120,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='category',label='Category',kind='select',required=False,nullable=False,max_length=80,choices=['measurement', 'defect', 'alarm', 'quality'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='context',label='Context',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['category'],sort_keys=['sample_label', 'process', 'metric', 'value', 'unit', 'sampled_at', 'subgroup', 'lot', 'category', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['sample_label', 'process', 'metric', 'value', 'unit', 'sampled_at', 'subgroup', 'lot', 'category', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'spc', 'timeline', 'dashboard'],visualizations=['spc', 'table', 'timeline', 'dashboard'])
