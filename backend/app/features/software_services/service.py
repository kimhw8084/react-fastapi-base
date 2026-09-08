from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import SoftwareService
from .schemas import SoftwareServiceCreate,SoftwareServiceRead,SoftwareServicePage,SoftwareServiceBulkRequest
WORKSPACE='software_services'
SORTS={'name':SoftwareService.name,'status':SoftwareService.status,'tier':SoftwareService.tier,'owner':SoftwareService.owner,'repository':SoftwareService.repository,'runtime':SoftwareService.runtime,'environment':SoftwareService.environment,'updated_at':SoftwareService.updated_at,'created_at':SoftwareService.created_at,'created_by':SoftwareService.created_by,'revision':SoftwareService.revision}
CRUD=RevisionCrudService(model=SoftwareService,create_schema=SoftwareServiceCreate,read_schema=SoftwareServiceRead,workspace=WORKSPACE,not_found_label='Service')
QUERY=EntityQueryService(model=SoftwareService,read_schema=SoftwareServiceRead,sorts=SORTS,search_columns=(SoftwareService.name,SoftwareService.owner,SoftwareService.repository,SoftwareService.runtime,SoftwareService.description,),filters={'status':(SoftwareService.status,('healthy', 'degraded', 'maintenance', 'retired')),'tier':(SoftwareService.tier,('tier_0', 'tier_1', 'tier_2', 'tier_3')),'environment':(SoftwareService.environment,('development', 'test', 'staging', 'production'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=SoftwareServicePage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:SoftwareServiceBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
