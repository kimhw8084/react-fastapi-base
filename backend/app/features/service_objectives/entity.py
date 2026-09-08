from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import ServiceObjective
from . import service
def _ref(row):return EntityReference(entity='service_objectives',id=row.id,label=str(getattr(row,'name')),workspace='service_objectives',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(ServiceObjective,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(ServiceObjective.name.ilike(f'%{escaped}%',escape='\\'),ServiceObjective.notes.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(ServiceObjective).where(*where).order_by(ServiceObjective.archived,ServiceObjective.name,ServiceObjective.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='service_objectives',label='Service objectives',description='Canonical SLO/error-budget records with server-owned burn and remaining-budget calculations.',workspace='service_objectives',primary_field='name',authority='canonical',search_fields=['name', 'notes'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
