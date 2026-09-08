from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import ObservabilityEvent
from . import service
def _ref(row):return EntityReference(entity='observability_events',id=row.id,label=str(getattr(row,'event_id')),workspace='observability_events',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(ObservabilityEvent,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(ObservabilityEvent.event_id.ilike(f'%{escaped}%',escape='\\'),ObservabilityEvent.trace_id.ilike(f'%{escaped}%',escape='\\'),ObservabilityEvent.span_id.ilike(f'%{escaped}%',escape='\\'),ObservabilityEvent.parent_span_id.ilike(f'%{escaped}%',escape='\\'),ObservabilityEvent.operation.ilike(f'%{escaped}%',escape='\\'),ObservabilityEvent.message.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(ObservabilityEvent).where(*where).order_by(ObservabilityEvent.archived,ObservabilityEvent.event_id,ObservabilityEvent.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='observability_events',label='Observability events',description='Canonical log, trace and metric events for reusable observability workspaces.',workspace='observability_events',primary_field='event_id',authority='canonical',search_fields=['event_id', 'trace_id', 'span_id', 'parent_span_id', 'operation', 'message'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
