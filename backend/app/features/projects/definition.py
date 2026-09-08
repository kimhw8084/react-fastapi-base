from app.platform.schemas import FieldDefinition, WorkspaceDefinition
from .schemas import ProjectCreate
from .service import SORTS
LABELS={'title':'Title','summary':'Summary','status':'Status','owner':'Owner'}
def definition()->WorkspaceDefinition:
    schema=ProjectCreate.model_json_schema();required=schema.get('required',[])
    fields=[]
    for key,value in schema['properties'].items():
        fields.append(FieldDefinition(key=key,label=LABELS[key],kind='select' if 'enum' in value else 'textarea' if key=='summary' else 'text',required=key in required,max_length=value.get('maxLength'),choices=value.get('enum',[])))
    return WorkspaceDefinition(key='projects',label='Projects',description='Canonical project records linked to work, knowledge, risk and planning projections.',fields=fields,filter_keys=['status'],sort_keys=list(SORTS),columns=['title','status','owner','updated_at','revision'],capabilities=['search','filters','sorting','selection','bulk','saved_views','details','history','compare','archive','restore','relationships','board'],visualizations=['table','board','dashboard','timeline','calendar','gantt','graph'])
