from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import KnowledgeEntrie
from . import service
def _ref(row):return EntityReference(entity='knowledge_entries',id=row.id,label=str(getattr(row,'title')),workspace='knowledge_entries',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(KnowledgeEntrie,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(KnowledgeEntrie.title.ilike(f'%{escaped}%',escape='\\'),KnowledgeEntrie.owner.ilike(f'%{escaped}%',escape='\\'),KnowledgeEntrie.content.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(KnowledgeEntrie).where(*where).order_by(KnowledgeEntrie.archived,KnowledgeEntrie.title,KnowledgeEntrie.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='knowledge_entries',label='Knowledge',description='Canonical engineering knowledge, procedures, runbooks and lessons linked to operational records.',workspace='knowledge_entries',primary_field='title',authority='canonical',search_fields=['title', 'owner', 'content'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
