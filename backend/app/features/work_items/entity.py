from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition, EntityReference
from .models import WorkItem
from . import service

def _reference(item: WorkItem) -> EntityReference:
    return EntityReference(entity='work_items',id=item.id,label=item.title,workspace='work_items',archived=item.archived,revision=item.revision)

def resolve(session: Session, record_id: str):
    item=session.get(WorkItem,record_id)
    return _reference(item) if item else None

def search(session: Session, query: str, limit: int):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        where.append(or_(WorkItem.title.ilike(f'%{escaped}%',escape='\\'),WorkItem.description.ilike(f'%{escaped}%',escape='\\')))
    rows=session.scalars(select(WorkItem).where(*where).order_by(WorkItem.archived,WorkItem.title,WorkItem.id).limit(limit)).all()
    return [_reference(item) for item in rows]

def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding() -> EntityBinding:
    return EntityBinding(EntityDefinition(
        key='work_items',label='Work items',description='Canonical work records used by multiple visualizations.',
        workspace='work_items',primary_field='title',authority='canonical',search_fields=['title','description'],
        capabilities=['history','archive','saved_views','attachments'],
    ),resolve,search,bulk_update=bulk_update)
