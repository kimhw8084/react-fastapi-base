from app.packs.semiconductor.models import normalize_lot
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import ManufacturingLot
from .schemas import ManufacturingLotCreate,ManufacturingLotRead,ManufacturingLotPage,ManufacturingLotBulkRequest
WORKSPACE='manufacturing_lots'
SORTS={'lot_id':ManufacturingLot.lot_id,'product':ManufacturingLot.product,'status':ManufacturingLot.status,'current_step':ManufacturingLot.current_step,'priority':ManufacturingLot.priority,'quantity':ManufacturingLot.quantity,'started_at':ManufacturingLot.started_at,'target_complete':ManufacturingLot.target_complete,'owner':ManufacturingLot.owner,'updated_at':ManufacturingLot.updated_at,'created_at':ManufacturingLot.created_at,'created_by':ManufacturingLot.created_by,'revision':ManufacturingLot.revision}
CRUD=RevisionCrudService(model=ManufacturingLot,create_schema=ManufacturingLotCreate,read_schema=ManufacturingLotRead,workspace=WORKSPACE,not_found_label='Lot',normalize_values=normalize_lot)
QUERY=EntityQueryService(model=ManufacturingLot,read_schema=ManufacturingLotRead,sorts=SORTS,search_columns=(ManufacturingLot.lot_id,ManufacturingLot.product,ManufacturingLot.current_step,ManufacturingLot.hold_reason,ManufacturingLot.owner,),filters={'status':(ManufacturingLot.status,('queued', 'running', 'hold', 'complete', 'scrapped')),'priority':(ManufacturingLot.priority,('low', 'normal', 'high', 'hot'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=ManufacturingLotPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:ManufacturingLotBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
