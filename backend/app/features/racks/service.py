from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import Rack
from .schemas import RackCreate,RackRead,RackPage,RackBulkRequest
WORKSPACE='racks'
SORTS={'name':Rack.name,'site':Rack.site,'row_name':Rack.row_name,'rack_units':Rack.rack_units,'power_capacity_kw':Rack.power_capacity_kw,'weight_capacity_kg':Rack.weight_capacity_kg,'thermal_capacity_kw':Rack.thermal_capacity_kw,'status':Rack.status,'updated_at':Rack.updated_at,'created_at':Rack.created_at,'created_by':Rack.created_by,'revision':Rack.revision}
CRUD=RevisionCrudService(model=Rack,create_schema=RackCreate,read_schema=RackRead,workspace=WORKSPACE,not_found_label='Rack')
QUERY=EntityQueryService(model=Rack,read_schema=RackRead,sorts=SORTS,search_columns=(Rack.name,Rack.site,Rack.row_name,),filters={'status':(Rack.status,('active', 'maintenance', 'retired'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=RackPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:RackBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
