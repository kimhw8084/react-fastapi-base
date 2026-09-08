from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import Risk
from .schemas import RiskCreate,RiskRead,RiskPage,RiskBulkRequest
WORKSPACE='risks'
SORTS={'title':Risk.title,'status':Risk.status,'category':Risk.category,'severity':Risk.severity,'occurrence':Risk.occurrence,'detection':Risk.detection,'rpn':Risk.rpn,'residual_severity':Risk.residual_severity,'residual_occurrence':Risk.residual_occurrence,'residual_detection':Risk.residual_detection,'residual_rpn':Risk.residual_rpn,'updated_at':Risk.updated_at,'created_at':Risk.created_at,'created_by':Risk.created_by,'revision':Risk.revision}
def normalize_risk(values):
    values=dict(values)
    values['rpn']=int(values['severity'])*int(values['occurrence'])*int(values['detection'])
    residual=(values.get('residual_severity'),values.get('residual_occurrence'),values.get('residual_detection'))
    values['residual_rpn']=int(residual[0])*int(residual[1])*int(residual[2]) if all(value is not None for value in residual) else None
    return values
CRUD=RevisionCrudService(model=Risk,create_schema=RiskCreate,read_schema=RiskRead,workspace=WORKSPACE,not_found_label='Risk',normalize_values=normalize_risk)
QUERY=EntityQueryService(model=Risk,read_schema=RiskRead,sorts=SORTS,search_columns=(Risk.title,Risk.effect,),filters={'status':(Risk.status,('identified', 'assessing', 'mitigating', 'monitoring', 'closed')),'category':(Risk.category,('design', 'process', 'hardware', 'software', 'network', 'human', 'environment'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=RiskPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:RiskBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
