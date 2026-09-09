from app.packs.semiconductor.models import normalize_equipment_state
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import EquipmentState
from .schemas import EquipmentStateCreate,EquipmentStateRead,EquipmentStatePage,EquipmentStateBulkRequest
WORKSPACE='equipment_states'
SORTS={'label':EquipmentState.label,'state':EquipmentState.state,'module':EquipmentState.module,'started_at':EquipmentState.started_at,'ended_at':EquipmentState.ended_at,'duration_minutes':EquipmentState.duration_minutes,'alarm_code':EquipmentState.alarm_code,'updated_at':EquipmentState.updated_at,'created_at':EquipmentState.created_at,'created_by':EquipmentState.created_by,'revision':EquipmentState.revision}
CRUD=RevisionCrudService(model=EquipmentState,create_schema=EquipmentStateCreate,read_schema=EquipmentStateRead,workspace=WORKSPACE,not_found_label='Equipment State',computed_values=normalize_equipment_state,computed_fields=('duration_minutes',))
QUERY=EntityQueryService(model=EquipmentState,read_schema=EquipmentStateRead,sorts=SORTS,search_columns=(EquipmentState.label,EquipmentState.module,EquipmentState.reason,EquipmentState.alarm_code,),filters={'state':(EquipmentState.state,('production', 'standby', 'engineering', 'scheduled_down', 'unscheduled_down'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=EquipmentStatePage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:EquipmentStateBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
