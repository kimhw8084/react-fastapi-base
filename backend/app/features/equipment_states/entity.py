from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import EquipmentState
from . import service
def _ref(row):return EntityReference(entity='equipment_states',id=row.id,label=str(getattr(row,'label')),workspace='equipment_states',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(EquipmentState,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(EquipmentState.label.ilike(f'%{escaped}%',escape='\\'),EquipmentState.module.ilike(f'%{escaped}%',escape='\\'),EquipmentState.reason.ilike(f'%{escaped}%',escape='\\'),EquipmentState.alarm_code.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(EquipmentState).where(*where).order_by(EquipmentState.archived,EquipmentState.label,EquipmentState.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='equipment_states',label='Equipment states',description='Canonical equipment/module state intervals for utilization, downtime and reason analysis.',workspace='equipment_states',primary_field='label',authority='canonical',search_fields=['label', 'module', 'reason', 'alarm_code'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
