from app.packs.software_engineering.models import normalize_delivery
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import DeliveryRun
from .schemas import DeliveryRunCreate,DeliveryRunRead,DeliveryRunPage,DeliveryRunBulkRequest
WORKSPACE='delivery_runs'
SORTS={'run_id':DeliveryRun.run_id,'status':DeliveryRun.status,'environment':DeliveryRun.environment,'commit_sha':DeliveryRun.commit_sha,'branch':DeliveryRun.branch,'started_at':DeliveryRun.started_at,'completed_at':DeliveryRun.completed_at,'duration_minutes':DeliveryRun.duration_minutes,'triggered_by':DeliveryRun.triggered_by,'updated_at':DeliveryRun.updated_at,'created_at':DeliveryRun.created_at,'created_by':DeliveryRun.created_by,'revision':DeliveryRun.revision}
CRUD=RevisionCrudService(model=DeliveryRun,create_schema=DeliveryRunCreate,read_schema=DeliveryRunRead,workspace=WORKSPACE,not_found_label='Delivery Run',normalize_values=normalize_delivery)
QUERY=EntityQueryService(model=DeliveryRun,read_schema=DeliveryRunRead,sorts=SORTS,search_columns=(DeliveryRun.run_id,DeliveryRun.commit_sha,DeliveryRun.branch,DeliveryRun.triggered_by,),filters={'status':(DeliveryRun.status,('queued', 'running', 'passed', 'failed', 'cancelled')),'environment':(DeliveryRun.environment,('development', 'test', 'staging', 'production'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=DeliveryRunPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:DeliveryRunBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
