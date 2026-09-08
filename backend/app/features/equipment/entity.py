from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import Equipment
from . import service
def _ref(row):return EntityReference(entity='equipment',id=row.id,label=str(getattr(row,'name')),workspace='equipment',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(Equipment,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(Equipment.name.ilike(f'%{escaped}%',escape='\\'),Equipment.serial.ilike(f'%{escaped}%',escape='\\'),Equipment.notes.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(Equipment).where(*where).order_by(Equipment.archived,Equipment.name,Equipment.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='equipment',label='Equipment',description='Canonical equipment records placed into physical layouts without copying identity data.',workspace='equipment',primary_field='name',authority='canonical',search_fields=['name', 'serial', 'notes'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
