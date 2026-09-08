from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import ProcessRecipe
from . import service
def _ref(row):return EntityReference(entity='process_recipes',id=row.id,label=str(getattr(row,'name')),workspace='process_recipes',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(ProcessRecipe,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(ProcessRecipe.name.ilike(f'%{escaped}%',escape='\\'),ProcessRecipe.version_name.ilike(f'%{escaped}%',escape='\\'),ProcessRecipe.process.ilike(f'%{escaped}%',escape='\\'),ProcessRecipe.approved_by.ilike(f'%{escaped}%',escape='\\'),ProcessRecipe.notes.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(ProcessRecipe).where(*where).order_by(ProcessRecipe.archived,ProcessRecipe.name,ProcessRecipe.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='process_recipes',label='Process recipes',description='Canonical versioned process recipe records with structured parameters, limits and approval context.',workspace='process_recipes',primary_field='name',authority='canonical',search_fields=['name', 'version_name', 'process', 'approved_by', 'notes'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
