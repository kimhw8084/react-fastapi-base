from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import ProcessMeasurement
from . import service
def _ref(row):return EntityReference(entity='process_measurements',id=row.id,label=str(getattr(row,'sample_label')),workspace='process_measurements',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(ProcessMeasurement,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(ProcessMeasurement.sample_label.ilike(f'%{escaped}%',escape='\\'),ProcessMeasurement.process.ilike(f'%{escaped}%',escape='\\'),ProcessMeasurement.metric.ilike(f'%{escaped}%',escape='\\'),ProcessMeasurement.unit.ilike(f'%{escaped}%',escape='\\'),ProcessMeasurement.subgroup.ilike(f'%{escaped}%',escape='\\'),ProcessMeasurement.lot.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(ProcessMeasurement).where(*where).order_by(ProcessMeasurement.archived,ProcessMeasurement.sample_label,ProcessMeasurement.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='process_measurements',label='Process measurements',description='Canonical engineering measurement samples for SPC, capability, trend and trace analysis.',workspace='process_measurements',primary_field='sample_label',authority='canonical',search_fields=['sample_label', 'process', 'metric', 'unit', 'subgroup', 'lot'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
