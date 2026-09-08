from app.platform.schemas import FieldDefinition, WorkspaceDefinition
from .schemas import WorkItemCreate
from .service import SORTS

# Field choices/requiredness are derived from Pydantic; labels are app-owned.
LABELS = {'title':'Title','description':'Description','status':'Status','priority':'Priority'}

def definition() -> WorkspaceDefinition:
    schema = WorkItemCreate.model_json_schema()
    required = schema.get('required', [])
    fields = []
    for key, value in schema['properties'].items():
        fields.append(FieldDefinition(
            key=key, label=LABELS[key], kind='select' if 'enum' in value else 'textarea' if key == 'description' else 'text',
            required=key in required, max_length=value.get('maxLength'), choices=value.get('enum', []),
        ))
    return WorkspaceDefinition(
        key='work_items', label='Work items',
        description='A complete reference workflow with shared views, version history and protected changes.',
        fields=fields,
        filter_keys=['status','priority'],
        sort_keys=list(SORTS),
        columns=['title','status','priority','created_by','updated_at','revision'],
        capabilities=['search','filters','sorting','selection','bulk','saved_views','details','history','compare','archive','restore','csv','attachments','board'],
        visualizations=['table','board','dashboard','timeline','calendar','gantt','graph'],
    )
