from app.platform.schemas import FieldDefinition,WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='diagram_documents',label='Diagram studio',description='Canonical architecture, workflow, topology and process diagrams with validated nodes and edges.',primary_field='title',fields=[
        FieldDefinition(key='title',label='Title',kind='text',required=True,nullable=False,max_length=200,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='diagram_type',label='Diagram type',kind='select',required=False,nullable=False,max_length=80,choices=['architecture', 'workflow', 'data_flow', 'topology', 'process', 'state_machine', 'lineage'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='status',label='Status',kind='select',required=False,nullable=False,max_length=80,choices=['draft', 'active', 'in_review', 'retired'],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='nodes',label='Nodes',kind='json',required=False,nullable=False,max_length=300000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='edges',label='Edges',kind='json',required=False,nullable=False,max_length=300000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='viewport',label='Viewport',kind='json',required=False,nullable=False,max_length=20000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False),
        FieldDefinition(key='node_count',label='Node count',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=1000,step=None,unit=None,read_only=True),
        FieldDefinition(key='edge_count',label='Edge count',kind='integer',required=False,nullable=False,max_length=None,choices=[],minimum=0,maximum=3000,step=None,unit=None,read_only=True),
        FieldDefinition(key='notes',label='Notes',kind='markdown',required=False,nullable=True,max_length=50000,choices=[],minimum=None,maximum=None,step=None,unit=None,read_only=False)
    ],filter_keys=['diagram_type', 'status'],sort_keys=['title', 'diagram_type', 'status', 'node_count', 'edge_count', 'updated_at', 'created_at', 'created_by', 'revision'],columns=['title', 'diagram_type', 'status', 'node_count', 'edge_count', 'updated_at', 'revision'],capabilities=['search', 'filters', 'sorting', 'selection', 'bulk', 'saved_views', 'details', 'history', 'compare', 'archive', 'restore', 'relationships', 'dashboard', 'graph'],visualizations=['designer','table','dashboard','graph'])
