from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import DeliveryRun
from . import service
def _ref(row):return EntityReference(entity='delivery_runs',id=row.id,label=str(getattr(row,'run_id')),workspace='delivery_runs',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(DeliveryRun,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(DeliveryRun.run_id.ilike(f'%{escaped}%',escape='\\'),DeliveryRun.commit_sha.ilike(f'%{escaped}%',escape='\\'),DeliveryRun.branch.ilike(f'%{escaped}%',escape='\\'),DeliveryRun.triggered_by.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(DeliveryRun).where(*where).order_by(DeliveryRun.archived,DeliveryRun.run_id,DeliveryRun.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='delivery_runs',label='Delivery runs',description='Canonical CI/CD pipeline and deployment execution records.',workspace='delivery_runs',primary_field='run_id',authority='canonical',search_fields=['run_id', 'commit_sha', 'branch', 'triggered_by'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
