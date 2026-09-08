from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import Investigation
from .schemas import InvestigationCreate,InvestigationRead,InvestigationPage,InvestigationBulkRequest
WORKSPACE='investigations'
SORTS={'title':Investigation.title,'status':Investigation.status,'priority':Investigation.priority,'updated_at':Investigation.updated_at,'created_at':Investigation.created_at,'created_by':Investigation.created_by,'revision':Investigation.revision}
CRUD=RevisionCrudService(model=Investigation,create_schema=InvestigationCreate,read_schema=InvestigationRead,workspace=WORKSPACE,not_found_label='Investigation')
QUERY=EntityQueryService(model=Investigation,read_schema=InvestigationRead,sorts=SORTS,search_columns=(Investigation.title,Investigation.problem,Investigation.findings,Investigation.conclusion,),filters={'status':(Investigation.status,('open', 'investigating', 'validated', 'resolved', 'closed')),'priority':(Investigation.priority,('low', 'medium', 'high', 'critical'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=InvestigationPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:InvestigationBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
