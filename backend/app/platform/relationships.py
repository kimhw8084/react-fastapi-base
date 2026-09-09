from __future__ import annotations
from uuid import uuid4
import json
from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session
from app.platform.audit import record_event
from app.platform.entity_registry import EntityRegistry
from app.platform.errors import AppError
from app.platform.models import AuditEvent, EntityRelationship, utcnow
from app.platform.schemas import EntityReference, RelationshipCreate, RelationshipRead, RelationshipUpdate
from app.platform.security import Actor

WORKSPACE='relationships'

def _snapshot(row: EntityRelationship, source: EntityReference, target: EntityReference) -> dict:
    return RelationshipRead(
        id=row.id,definition_key=row.definition_key,source=source,target=target,metadata=row.metadata_json or {},
        revision=row.revision,archived=row.archived,created_by=row.created_by,created_at=row.created_at,updated_at=row.updated_at,
    ).model_dump(mode='json')

def _read(session: Session, registry: EntityRegistry, row: EntityRelationship) -> RelationshipRead:
    source=registry.resolve(session,row.source_entity,row.source_id)
    target=registry.resolve(session,row.target_entity,row.target_id)
    return RelationshipRead(
        id=row.id,definition_key=row.definition_key,source=source,target=target,metadata=row.metadata_json or {},
        revision=row.revision,archived=row.archived,created_by=row.created_by,created_at=row.created_at,updated_at=row.updated_at,
    )

def _require(session: Session, relationship_id: str) -> EntityRelationship:
    row=session.get(EntityRelationship,relationship_id)
    if row is None:
        raise AppError(404,'relationship_missing','Relationship was not found in this tenant.')
    return row

def _cardinality_guard(session: Session, definition, source_id: str, target_id: str, exclude_id: str|None=None) -> None:
    active=[EntityRelationship.definition_key==definition.key,EntityRelationship.archived.is_(False)]
    if exclude_id:
        active.append(EntityRelationship.id!=exclude_id)
    if definition.cardinality in ('one_to_one','many_to_one'):
        if session.scalar(select(EntityRelationship.id).where(*active,EntityRelationship.source_id==source_id).limit(1)):
            raise AppError(409,'relationship_cardinality','Source record already has the maximum active relationship of this type.')
    if definition.cardinality in ('one_to_one','one_to_many'):
        if session.scalar(select(EntityRelationship.id).where(*active,EntityRelationship.target_id==target_id).limit(1)):
            raise AppError(409,'relationship_cardinality','Target record already has the maximum active relationship of this type.')


def _acyclic_guard(session: Session, definition, source_id: str, target_id: str, exclude_id: str|None=None) -> None:
    if not getattr(definition,'acyclic',False):
        return
    if source_id==target_id:
        raise AppError(409,'relationship_cycle','Acyclic relationships cannot link a record to itself.')
    where=[EntityRelationship.definition_key==definition.key,EntityRelationship.archived.is_(False)]
    if exclude_id:where.append(EntityRelationship.id!=exclude_id)
    rows=session.scalars(select(EntityRelationship).where(*where)).all()
    adjacency:dict[str,list[str]]={}
    for row in rows:
        adjacency.setdefault(row.source_id,[]).append(row.target_id)
    stack=[target_id];seen=set()
    while stack:
        current=stack.pop()
        if current==source_id:
            raise AppError(409,'relationship_cycle','This relationship would create a cycle.')
        if current in seen:continue
        seen.add(current);stack.extend(adjacency.get(current,()))

def _validated_metadata(definition, metadata: dict) -> dict:
    try:
        encoded=json.dumps(metadata,separators=(',',':'),sort_keys=True)
    except (TypeError,ValueError) as error:
        raise AppError(422,'invalid_relationship_metadata','Relationship metadata must be JSON serializable.') from error
    if len(encoded.encode('utf-8'))>16384:
        raise AppError(422,'relationship_metadata_too_large','Relationship metadata exceeds 16 KiB.')
    if any(not isinstance(key,str) or not 1<=len(key)<=60 for key in metadata):
        raise AppError(422,'invalid_relationship_metadata','Relationship metadata keys must be 1-60 character strings.')
    if definition.kind=='connection':
        allowed={'source_port','target_port','cable_id','medium','protocol','status','length_m','label'}
        unknown=set(metadata)-allowed
        if unknown:raise AppError(422,'invalid_connection_metadata','Unsupported connection metadata.',{'keys':sorted(unknown)})
        source_port=metadata.get('source_port');target_port=metadata.get('target_port')
        if not isinstance(source_port,str) or not 1<=len(source_port.strip())<=64 or not isinstance(target_port,str) or not 1<=len(target_port.strip())<=64:raise AppError(422,'invalid_connection_metadata','source_port and target_port are required 1-64 character strings.')
        medium=metadata.get('medium','other');status=metadata.get('status','connected');protocol=metadata.get('protocol','');cable_id=metadata.get('cable_id','');label=metadata.get('label','');length=metadata.get('length_m')
        if medium not in ('fiber','copper','dac','wireless','logical','other'):raise AppError(422,'invalid_connection_metadata','Unsupported connection medium.')
        if status not in ('connected','planned','disabled','fault'):raise AppError(422,'invalid_connection_metadata','Unsupported connection status.')
        for name,value,limit in [('protocol',protocol,40),('cable_id',cable_id,120),('label',label,160)]:
            if not isinstance(value,str) or len(value)>limit:raise AppError(422,'invalid_connection_metadata',f'{name} is invalid.')
        if length is not None and (isinstance(length,bool) or not isinstance(length,(int,float)) or length<0 or length>100000):raise AppError(422,'invalid_connection_metadata','length_m must be between 0 and 100000.')
        return {'source_port':source_port.strip(),'target_port':target_port.strip(),'cable_id':cable_id.strip(),'medium':medium,'protocol':protocol.strip(),'status':status,'length_m':length,'label':label.strip()}
    if definition.kind!='placement':
        return dict(metadata)
    allowed={'start_unit','size_u','face'}
    unknown=set(metadata)-allowed
    if unknown:
        raise AppError(422,'invalid_placement_metadata','Unsupported rack placement metadata.',{'keys':sorted(unknown)})
    start=metadata.get('start_unit');size=metadata.get('size_u');face=metadata.get('face','front')
    if isinstance(start,bool) or not isinstance(start,int) or start<1:
        raise AppError(422,'invalid_placement_metadata','start_unit must be a positive integer.')
    if isinstance(size,bool) or not isinstance(size,int) or size<1:
        raise AppError(422,'invalid_placement_metadata','size_u must be a positive integer.')
    if face not in ('front','rear'):
        raise AppError(422,'invalid_placement_metadata','face must be front or rear.')
    capacity=definition.placement_capacity or 0
    if start+size-1>capacity:
        raise AppError(409,'placement_out_of_bounds',f'Placement exceeds configured rack capacity of {capacity}U.')
    return {'start_unit':start,'size_u':size,'face':face}

def _placement_guard(session: Session, definition, source_id: str, metadata: dict, exclude_id: str|None=None) -> None:
    if definition.kind!='placement':
        return
    start=metadata['start_unit'];end=start+metadata['size_u']-1;face=metadata['face']
    where=[EntityRelationship.definition_key==definition.key,EntityRelationship.source_id==source_id,EntityRelationship.archived.is_(False)]
    if exclude_id:where.append(EntityRelationship.id!=exclude_id)
    for row in session.scalars(select(EntityRelationship).where(*where)).all():
        current=row.metadata_json or {}
        if current.get('face','front')!=face:continue
        other_start=current.get('start_unit');other_size=current.get('size_u')
        if isinstance(other_start,int) and isinstance(other_size,int):
            other_end=other_start+other_size-1
            if not (end<other_start or start>other_end):
                raise AppError(409,'placement_collision',f'Rack units U{start}-U{end} collide with an existing placement.')

def _connection_guard(session: Session, definition, source_id: str, target_id: str, metadata: dict, exclude_id: str|None=None) -> None:
    if definition.kind!='connection':return
    candidate={(source_id,metadata['source_port'].casefold()),(target_id,metadata['target_port'].casefold())}
    where=[EntityRelationship.definition_key==definition.key,EntityRelationship.archived.is_(False)]
    if exclude_id:where.append(EntityRelationship.id!=exclude_id)
    for row in session.scalars(select(EntityRelationship).where(*where)).all():
        current=row.metadata_json or {};source_port=current.get('source_port');target_port=current.get('target_port')
        occupied=set()
        if isinstance(source_port,str):occupied.add((row.source_id,source_port.casefold()))
        if isinstance(target_port,str):occupied.add((row.target_id,target_port.casefold()))
        if candidate & occupied:raise AppError(409,'port_occupied','One of the selected connection ports is already occupied.')

def create(session: Session, actor: Actor, registry: EntityRegistry, data: RelationshipCreate) -> RelationshipRead:
    actor.require('write')
    definition=registry.relationship(data.definition_key)
    if definition.source_entity==definition.target_entity and data.source_id==data.target_id and not definition.allow_self:
        raise AppError(422,'self_relationship','This relationship type does not allow a record to link to itself.')
    source=registry.resolve(session,definition.source_entity,data.source_id)
    target=registry.resolve(session,definition.target_entity,data.target_id)
    existing=None if definition.allow_parallel else session.scalar(select(EntityRelationship).where(
        EntityRelationship.definition_key==definition.key,
        EntityRelationship.source_id==data.source_id,EntityRelationship.target_id==data.target_id))
    if existing:
        if existing.archived:
            raise AppError(409,'relationship_archived','This relationship already exists in archived state; restore it instead.')
        raise AppError(409,'relationship_exists','This relationship already exists.')
    metadata=_validated_metadata(definition,data.metadata)
    _cardinality_guard(session,definition,data.source_id,data.target_id)
    _acyclic_guard(session,definition,data.source_id,data.target_id)
    _placement_guard(session,definition,data.source_id,metadata)
    _connection_guard(session,definition,data.source_id,data.target_id,metadata)
    row=EntityRelationship(
        id=str(uuid4()),definition_key=definition.key,source_entity=definition.source_entity,source_id=data.source_id,
        target_entity=definition.target_entity,target_id=data.target_id,metadata_json=metadata,revision=1,archived=False,created_by=actor.user_id)
    session.add(row);session.flush()
    after=_snapshot(row,source,target)
    record_event(session,actor,workspace=WORKSPACE,entity_id=row.id,action='create',revision=1,before=None,after=after)
    return RelationshipRead.model_validate(after)

def list_for_record(session: Session, actor: Actor, registry: EntityRegistry, entity: str, record_id: str, *, include_archived: bool=False) -> list[RelationshipRead]:
    actor.require('read')
    registry.resolve(session,entity,record_id)
    where=[or_(and_(EntityRelationship.source_entity==entity,EntityRelationship.source_id==record_id),and_(EntityRelationship.target_entity==entity,EntityRelationship.target_id==record_id))]
    if not include_archived:
        where.append(EntityRelationship.archived.is_(False))
    rows=session.scalars(select(EntityRelationship).where(*where).order_by(EntityRelationship.updated_at.desc(),EntityRelationship.id).limit(500)).all()
    return [_read(session,registry,row) for row in rows]

def list_for_entity(session: Session, actor: Actor, registry: EntityRegistry, entity: str, *, include_archived: bool=False, limit: int=500) -> list[RelationshipRead]:
    actor.require('read')
    registry.definition(entity)
    where=[or_(EntityRelationship.source_entity==entity,EntityRelationship.target_entity==entity)]
    if not include_archived:
        where.append(EntityRelationship.archived.is_(False))
    rows=session.scalars(select(EntityRelationship).where(*where).order_by(EntityRelationship.updated_at.desc(),EntityRelationship.id).limit(limit)).all()
    return [_read(session,registry,row) for row in rows]

def explore(session: Session, actor: Actor, registry: EntityRegistry, entity: str, record_id: str, *, kind: str|None=None, direction: str='both', depth: int=1, limit: int=200) -> list[RelationshipRead]:
    """Bounded graph traversal over canonical relationship rows.

    The traversal never follows a feature-owned shadow graph. It resolves every
    endpoint through the registry and carries tenant authorization from the
    request actor. ``incoming`` is useful for backlinks/upstream/impact and
    ``outgoing`` is useful for dependencies/downstream/connections.
    """
    actor.require('read')
    registry.resolve(session,entity,record_id)
    if direction not in {'both','incoming','outgoing'} or depth<1 or depth>8 or not 1<=limit<=1000:
        raise AppError(422,'invalid_relationship_explorer','Explorer bounds are invalid.')
    if kind is not None and kind not in {'reference','hierarchy','dependency','placement','causal','temporal','logical','connection'}:
        raise AppError(422,'invalid_relationship_explorer','Relationship kind is invalid.')
    frontier={(entity,record_id)};visited=set();result=[]
    for _level in range(depth):
        if not frontier or len(result)>=limit: break
        outgoing=[and_(EntityRelationship.source_entity==source,EntityRelationship.source_id==record) for source,record in frontier]
        incoming=[and_(EntityRelationship.target_entity==target,EntityRelationship.target_id==record) for target,record in frontier]
        edge_filters=[]
        if direction in {'both','outgoing'}: edge_filters.extend(outgoing)
        if direction in {'both','incoming'}: edge_filters.extend(incoming)
        if not edge_filters: break
        rows=session.scalars(select(EntityRelationship).where(EntityRelationship.archived.is_(False),or_(*edge_filters)).order_by(EntityRelationship.updated_at.desc(),EntityRelationship.id).limit(limit*4)).all()
        next_frontier=set()
        for row in rows:
            definition=registry.relationship(row.definition_key)
            if kind and definition.kind!=kind: continue
            source=(row.source_entity,row.source_id);target=(row.target_entity,row.target_id)
            matches=[]
            if direction in {'both','outgoing'} and source in frontier: matches.append(target)
            if direction in {'both','incoming'} and target in frontier: matches.append(source)
            if not matches: continue
            if row.id in visited: continue
            visited.add(row.id)
            result.append(_read(session,registry,row))
            next_frontier.update(matches)
            if len(result)>=limit: break
        frontier=next_frontier
    return result

def update_metadata(session: Session, actor: Actor, registry: EntityRegistry, relationship_id: str, data: RelationshipUpdate) -> RelationshipRead:
    actor.require('write')
    row=_require(session,relationship_id)
    if row.revision!=data.revision:
        raise AppError(409,'revision_conflict','Relationship changed. Refresh before retrying.',{'current':_read(session,registry,row).model_dump(mode='json')})
    if row.archived:
        raise AppError(409,'invalid_transition','Archived relationships cannot be edited until restored.')
    definition=registry.relationship(row.definition_key)
    metadata=_validated_metadata(definition,data.metadata)
    _placement_guard(session,definition,row.source_id,metadata,exclude_id=row.id)
    _connection_guard(session,definition,row.source_id,row.target_id,metadata,exclude_id=row.id)
    before=_read(session,registry,row).model_dump(mode='json')
    result=session.execute(update(EntityRelationship).where(EntityRelationship.id==row.id,EntityRelationship.revision==data.revision).values(metadata_json=metadata,revision=data.revision+1,updated_at=utcnow()),execution_options={'synchronize_session':False})
    if result.rowcount!=1:
        raise AppError(409,'revision_conflict','Relationship changed. Refresh before retrying.')
    session.refresh(row)
    after=_read(session,registry,row)
    record_event(session,actor,workspace=WORKSPACE,entity_id=row.id,action='update',revision=row.revision,before=before,after=after.model_dump(mode='json'))
    return after

def lifecycle(session: Session, actor: Actor, registry: EntityRegistry, relationship_id: str, expected_revision: int, action: str) -> RelationshipRead:
    actor.require('restore' if action=='restore' else 'write')
    if action not in ('archive','restore'):
        raise AppError(422,'invalid_action','Unsupported relationship lifecycle action.')
    row=_require(session,relationship_id)
    if row.revision!=expected_revision:
        raise AppError(409,'revision_conflict','Relationship changed. Refresh before retrying.',{'current':_read(session,registry,row).model_dump(mode='json')})
    target=action=='archive'
    if row.archived==target:
        raise AppError(409,'invalid_transition','Relationship is already in the requested state.')
    definition=registry.relationship(row.definition_key)
    if action=='restore':
        registry.resolve(session,row.source_entity,row.source_id);registry.resolve(session,row.target_entity,row.target_id)
        _cardinality_guard(session,definition,row.source_id,row.target_id,exclude_id=row.id)
        _acyclic_guard(session,definition,row.source_id,row.target_id,exclude_id=row.id)
        metadata=_validated_metadata(definition,row.metadata_json or {})
        _placement_guard(session,definition,row.source_id,metadata,exclude_id=row.id)
        _connection_guard(session,definition,row.source_id,row.target_id,metadata,exclude_id=row.id)
    before=_read(session,registry,row).model_dump(mode='json')
    result=session.execute(update(EntityRelationship).where(EntityRelationship.id==row.id,EntityRelationship.revision==expected_revision).values(archived=target,revision=expected_revision+1,updated_at=utcnow()),execution_options={'synchronize_session':False})
    if result.rowcount!=1:
        raise AppError(409,'revision_conflict','Relationship changed. Refresh before retrying.')
    session.refresh(row)
    after=_read(session,registry,row)
    record_event(session,actor,workspace=WORKSPACE,entity_id=row.id,action=action,revision=row.revision,before=before,after=after.model_dump(mode='json'))
    return after

def history(session: Session, actor: Actor, relationship_id: str) -> list[AuditEvent]:
    actor.require('read');_require(session,relationship_id)
    return list(session.scalars(select(AuditEvent).where(AuditEvent.workspace==WORKSPACE,AuditEvent.entity_id==relationship_id).order_by(AuditEvent.revision.desc()).limit(200)).all())
