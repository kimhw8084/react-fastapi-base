from app.platform.schemas import WorkspaceDefinition

def definition()->WorkspaceDefinition:
    return WorkspaceDefinition(key='system',label='System',description='Administration, diagnostics, notifications, integration endpoints and durable job operations.',fields=[],columns=[],capabilities=['administration','diagnostics','notifications','feature_flags','jobs','webhooks','audit'],primary_field='title',filter_keys=[],sort_keys=[],visualizations=['system'])
