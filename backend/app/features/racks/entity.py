from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import Rack
from . import service
def _ref(row):return EntityReference(entity='racks',id=row.id,label=str(getattr(row,'name')),workspace='racks',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(Rack,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(Rack.name.ilike(f'%{escaped}%',escape='\\'),Rack.site.ilike(f'%{escaped}%',escape='\\'),Rack.row_name.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(Rack).where(*where).order_by(Rack.archived,Rack.name,Rack.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='racks',label='Racks',description='Canonical physical rack records for reusable estate and placement workspaces.',workspace='racks',primary_field='name',authority='canonical',search_fields=['name', 'site', 'row_name'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
