from app.packs.software_engineering.models import normalize_slo
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import ServiceObjective
from .schemas import ServiceObjectiveCreate,ServiceObjectiveRead,ServiceObjectivePage,ServiceObjectiveBulkRequest
WORKSPACE='service_objectives'
SORTS={'name':ServiceObjective.name,'window_days':ServiceObjective.window_days,'target_percent':ServiceObjective.target_percent,'current_percent':ServiceObjective.current_percent,'error_budget_remaining':ServiceObjective.error_budget_remaining,'burn_rate':ServiceObjective.burn_rate,'status':ServiceObjective.status,'updated_at':ServiceObjective.updated_at,'created_at':ServiceObjective.created_at,'created_by':ServiceObjective.created_by,'revision':ServiceObjective.revision}
CRUD=RevisionCrudService(model=ServiceObjective,create_schema=ServiceObjectiveCreate,read_schema=ServiceObjectiveRead,workspace=WORKSPACE,not_found_label='Slo',normalize_values=normalize_slo)
QUERY=EntityQueryService(model=ServiceObjective,read_schema=ServiceObjectiveRead,sorts=SORTS,search_columns=(ServiceObjective.name,ServiceObjective.notes,),filters={'status':(ServiceObjective.status,('healthy', 'warning', 'exhausted'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=ServiceObjectivePage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:ServiceObjectiveBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
