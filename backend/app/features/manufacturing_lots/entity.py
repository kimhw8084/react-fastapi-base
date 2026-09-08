from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import ManufacturingLot
from . import service
def _ref(row):return EntityReference(entity='manufacturing_lots',id=row.id,label=str(getattr(row,'lot_id')),workspace='manufacturing_lots',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(ManufacturingLot,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(ManufacturingLot.lot_id.ilike(f'%{escaped}%',escape='\\'),ManufacturingLot.product.ilike(f'%{escaped}%',escape='\\'),ManufacturingLot.current_step.ilike(f'%{escaped}%',escape='\\'),ManufacturingLot.hold_reason.ilike(f'%{escaped}%',escape='\\'),ManufacturingLot.owner.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(ManufacturingLot).where(*where).order_by(ManufacturingLot.archived,ManufacturingLot.lot_id,ManufacturingLot.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='manufacturing_lots',label='Manufacturing lots',description='Canonical manufacturing lot traveler records with route, holds and scheduling context.',workspace='manufacturing_lots',primary_field='lot_id',authority='canonical',search_fields=['lot_id', 'product', 'current_step', 'hold_reason', 'owner'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
