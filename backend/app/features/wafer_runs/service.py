from app.packs.semiconductor.models import normalize_wafer
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import WaferRun
from .schemas import WaferRunCreate,WaferRunRead,WaferRunPage,WaferRunBulkRequest
WORKSPACE='wafer_runs'
SORTS={'wafer_id':WaferRun.wafer_id,'lot_id':WaferRun.lot_id,'process_step':WaferRun.process_step,'status':WaferRun.status,'total_die':WaferRun.total_die,'good_die':WaferRun.good_die,'defect_count':WaferRun.defect_count,'yield_percent':WaferRun.yield_percent,'completed_at':WaferRun.completed_at,'updated_at':WaferRun.updated_at,'created_at':WaferRun.created_at,'created_by':WaferRun.created_by,'revision':WaferRun.revision}
CRUD=RevisionCrudService(model=WaferRun,create_schema=WaferRunCreate,read_schema=WaferRunRead,workspace=WORKSPACE,not_found_label='Wafer Run',normalize_values=normalize_wafer)
QUERY=EntityQueryService(model=WaferRun,read_schema=WaferRunRead,sorts=SORTS,search_columns=(WaferRun.wafer_id,WaferRun.lot_id,WaferRun.process_step,WaferRun.notes,),filters={'status':(WaferRun.status,('queued', 'processing', 'complete', 'hold', 'scrapped'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=WaferRunPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:WaferRunBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
