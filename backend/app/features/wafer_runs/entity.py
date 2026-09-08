from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import WaferRun
from . import service
def _ref(row):return EntityReference(entity='wafer_runs',id=row.id,label=str(getattr(row,'wafer_id')),workspace='wafer_runs',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(WaferRun,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(WaferRun.wafer_id.ilike(f'%{escaped}%',escape='\\'),WaferRun.lot_id.ilike(f'%{escaped}%',escape='\\'),WaferRun.process_step.ilike(f'%{escaped}%',escape='\\'),WaferRun.notes.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(WaferRun).where(*where).order_by(WaferRun.archived,WaferRun.wafer_id,WaferRun.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='wafer_runs',label='Wafer runs',description='Canonical wafer result records with tested die/bin summaries and traceable process context.',workspace='wafer_runs',primary_field='wafer_id',authority='canonical',search_fields=['wafer_id', 'lot_id', 'process_step', 'notes'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
