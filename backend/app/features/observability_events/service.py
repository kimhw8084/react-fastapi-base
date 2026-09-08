from app.packs.software_engineering.models import normalize_observability
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import ObservabilityEvent
from .schemas import ObservabilityEventCreate,ObservabilityEventRead,ObservabilityEventPage,ObservabilityEventBulkRequest
WORKSPACE='observability_events'
SORTS={'event_id':ObservabilityEvent.event_id,'signal':ObservabilityEvent.signal,'severity':ObservabilityEvent.severity,'timestamp':ObservabilityEvent.timestamp,'duration_ms':ObservabilityEvent.duration_ms,'trace_id':ObservabilityEvent.trace_id,'span_id':ObservabilityEvent.span_id,'operation':ObservabilityEvent.operation,'updated_at':ObservabilityEvent.updated_at,'created_at':ObservabilityEvent.created_at,'created_by':ObservabilityEvent.created_by,'revision':ObservabilityEvent.revision}
CRUD=RevisionCrudService(model=ObservabilityEvent,create_schema=ObservabilityEventCreate,read_schema=ObservabilityEventRead,workspace=WORKSPACE,not_found_label='Event',normalize_values=normalize_observability)
QUERY=EntityQueryService(model=ObservabilityEvent,read_schema=ObservabilityEventRead,sorts=SORTS,search_columns=(ObservabilityEvent.event_id,ObservabilityEvent.trace_id,ObservabilityEvent.span_id,ObservabilityEvent.parent_span_id,ObservabilityEvent.operation,ObservabilityEvent.message,),filters={'signal':(ObservabilityEvent.signal,('log', 'trace', 'metric')),'severity':(ObservabilityEvent.severity,('debug', 'info', 'warning', 'error', 'critical'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=ObservabilityEventPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:ObservabilityEventBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
