from sqlalchemy import or_,select
from sqlalchemy.orm import Session
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import Project
from . import service

def _ref(row):return EntityReference(entity='projects',id=row.id,label=row.title,workspace='projects',archived=row.archived,revision=row.revision)
def resolve(session:Session,record_id:str):
    row=session.get(Project,record_id);return _ref(row) if row else None
def search(session:Session,query:str,limit:int):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        where.append(or_(Project.title.ilike(f'%{escaped}%',escape='\\'),Project.summary.ilike(f'%{escaped}%',escape='\\'),Project.owner.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(Project).where(*where).order_by(Project.archived,Project.title,Project.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='projects',label='Projects',description='Canonical project/program records.',workspace='projects',primary_field='title',authority='canonical',search_fields=['title','summary','owner'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
