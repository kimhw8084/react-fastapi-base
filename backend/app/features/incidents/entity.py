from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import Incident
from . import service
def _ref(row):return EntityReference(entity='incidents',id=row.id,label=str(getattr(row,'title')),workspace='incidents',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(Incident,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(Incident.incident_number.ilike(f'%{escaped}%',escape='\\'),Incident.title.ilike(f'%{escaped}%',escape='\\'),Incident.commander.ilike(f'%{escaped}%',escape='\\'),Incident.impact.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(Incident).where(*where).order_by(Incident.archived,Incident.title,Incident.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='incidents',label='Incidents',description='Canonical incident command records with timeline, impact, ownership and action context.',workspace='incidents',primary_field='title',authority='canonical',search_fields=['incident_number', 'title', 'commander', 'impact'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
