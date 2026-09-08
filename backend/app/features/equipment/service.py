from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import Equipment
from .schemas import EquipmentCreate,EquipmentRead,EquipmentPage,EquipmentBulkRequest
WORKSPACE='equipment'
SORTS={'name':Equipment.name,'kind':Equipment.kind,'status':Equipment.status,'serial':Equipment.serial,'power_kw':Equipment.power_kw,'updated_at':Equipment.updated_at,'created_at':Equipment.created_at,'created_by':Equipment.created_by,'revision':Equipment.revision}
CRUD=RevisionCrudService(model=Equipment,create_schema=EquipmentCreate,read_schema=EquipmentRead,workspace=WORKSPACE,not_found_label='Equipment Item')
QUERY=EntityQueryService(model=Equipment,read_schema=EquipmentRead,sorts=SORTS,search_columns=(Equipment.name,Equipment.serial,Equipment.notes,),filters={'kind':(Equipment.kind,('server', 'switch', 'storage', 'appliance', 'other')),'status':(Equipment.status,('active', 'maintenance', 'offline', 'retired'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=EquipmentPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:EquipmentBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
