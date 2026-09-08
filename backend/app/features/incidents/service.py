from app.packs.software_engineering.models import normalize_incident
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import Incident
from .schemas import IncidentCreate,IncidentRead,IncidentPage,IncidentBulkRequest
WORKSPACE='incidents'
SORTS={'incident_number':Incident.incident_number,'title':Incident.title,'status':Incident.status,'severity':Incident.severity,'started_at':Incident.started_at,'resolved_at':Incident.resolved_at,'duration_minutes':Incident.duration_minutes,'commander':Incident.commander,'updated_at':Incident.updated_at,'created_at':Incident.created_at,'created_by':Incident.created_by,'revision':Incident.revision}
CRUD=RevisionCrudService(model=Incident,create_schema=IncidentCreate,read_schema=IncidentRead,workspace=WORKSPACE,not_found_label='Incident',normalize_values=normalize_incident)
QUERY=EntityQueryService(model=Incident,read_schema=IncidentRead,sorts=SORTS,search_columns=(Incident.incident_number,Incident.title,Incident.commander,Incident.impact,),filters={'status':(Incident.status,('investigating', 'identified', 'monitoring', 'resolved', 'closed')),'severity':(Incident.severity,('sev_1', 'sev_2', 'sev_3', 'sev_4'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=IncidentPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:IncidentBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
