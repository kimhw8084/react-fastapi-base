from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import SoftwareService
from . import service
def _ref(row):return EntityReference(entity='software_services',id=row.id,label=str(getattr(row,'name')),workspace='software_services',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(SoftwareService,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(SoftwareService.name.ilike(f'%{escaped}%',escape='\\'),SoftwareService.owner.ilike(f'%{escaped}%',escape='\\'),SoftwareService.repository.ilike(f'%{escaped}%',escape='\\'),SoftwareService.runtime.ilike(f'%{escaped}%',escape='\\'),SoftwareService.description.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(SoftwareService).where(*where).order_by(SoftwareService.archived,SoftwareService.name,SoftwareService.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='software_services',label='Software services',description='Canonical software/service registry records used by delivery, observability, incidents and SLO workspaces.',workspace='software_services',primary_field='name',authority='canonical',search_fields=['name', 'owner', 'repository', 'runtime', 'description'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
