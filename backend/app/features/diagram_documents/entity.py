from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import DiagramDocument
from . import service
def _ref(row):return EntityReference(entity='diagram_documents',id=row.id,label=str(getattr(row,'title')),workspace='diagram_documents',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(DiagramDocument,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(DiagramDocument.title.ilike(f'%{escaped}%',escape='\\'),DiagramDocument.notes.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(DiagramDocument).where(*where).order_by(DiagramDocument.archived,DiagramDocument.title,DiagramDocument.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='diagram_documents',label='Diagram studio',description='Canonical architecture, workflow, topology and process diagrams with validated nodes and edges.',workspace='diagram_documents',primary_field='title',authority='canonical',search_fields=['title', 'notes'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
