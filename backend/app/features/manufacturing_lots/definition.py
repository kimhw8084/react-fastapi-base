from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='manufacturing_lots',label='Manufacturing lots',description='Canonical manufacturing lot traveler records with route, holds and scheduling context.',primary_field='lot_id',fields=[
        FieldDefinition(key='lot_id',label='Lot ID',kind='text',required=True,nullable=False,max_length=120,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='product',label='Product',kind='text',required=True,nullable=False,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['queued', 'running', 'hold', 'complete', 'scrapped'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='current_step',label='Current step',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='priority',label='Priority',kind='select',required=False,nullable=False,max_length=80,choices=['low', 'normal', 'high', 'hot'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='quantity',label='Quantity',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='started_at',label='Started at',kind='datetime',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='target_complete',label='Target complete',kind='datetime',required=False,nullable=True,max_length=None,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='route',label='Route',kind='json',required=False,nullable=False,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='hold_reason',label='Hold reason',kind='textarea',required=False,nullable=True,max_length=10000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='owner',label='Owner',kind='text',required=False,nullable=True,max_length=160,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['status', 'priority'],sort_keys=['lot_id', 'product', 'status', 'current_step', 'priority', 'quantity', 'started_at', 'target_complete', 'owner', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['lot_id', 'product', 'status', 'current_step', 'priority', 'quantity', 'started_at', 'target_complete', 'owner', 'updated_at', 'revision'],capabilities=['traveler', 'search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'board', 'timeline', 'calendar', 'dashboard'],visualizations=['traveler', 'table', 'board', 'timeline', 'calendar', 'dashboard'])
