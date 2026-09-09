from __future__ import annotations
from collections.abc import Callable, Mapping
from uuid import uuid4
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.platform.audit import record_event
from app.platform.errors import AppError
from app.platform.models import AuditEvent, utcnow
from app.platform.security import Actor
from app.platform.events import emit as emit_platform_event

class RevisionCrudService:
    """Reusable optimistic-concurrency/lifecycle/audit engine for tenant records.

    Feature code owns schemas, list semantics and business rules; this class owns the
    invariant mechanics that should not be rewritten in every CRUD workspace.
    """
    def __init__(self, *, model, create_schema, read_schema, workspace: str, not_found_label: str, normalize_values=None, computed_values: Callable[[dict], Mapping] | None = None, computed_fields: tuple[str, ...] = ()):
        self.model=model;self.create_schema=create_schema;self.read_schema=read_schema
        self.workspace=workspace;self.not_found_label=not_found_label;self.normalize_values=normalize_values
        self.computed_values=computed_values;self.computed_fields=tuple(computed_fields)

    def normalized(self, values: dict) -> dict:
        data=dict(values)
        if not self.normalize_values:
            normalized=data
        else:
            try:
                normalized=dict(self.normalize_values(data))
            except AppError:
                raise
            except ValueError as error:
                raise AppError(422,'domain_validation',str(error)) from error
        if self.computed_values:
            try:
                computed=dict(self.computed_values(dict(normalized)))
            except AppError:
                raise
            except ValueError as error:
                raise AppError(422,'computed_field_validation',str(error)) from error
            # Only the declared server-owned fields can be added by this hook.
            # A provider cannot smuggle arbitrary columns into a mutation.
            unknown=set(computed)-set(normalized)-set(self.computed_fields)
            if unknown:
                raise AppError(500,'computed_field_contract','Computed field resolver returned an undeclared field.')
            normalized.update({key:computed[key] for key in self.computed_fields if key in computed})
        return normalized

    def _computed_update(self, row, values: dict) -> dict:
        if not self.computed_values:
            return {}
        current={field:getattr(row,field) for field in self.create_schema.model_fields if hasattr(row,field)}
        merged={**current,**values}
        normalized=self.normalized(merged)
        return {key:normalized[key] for key in self.computed_fields if key in normalized}

    def require(self, session: Session, record_id: str):
        row=session.get(self.model,record_id)
        if row is None:
            raise AppError(404,'not_found',f'{self.not_found_label} was not found in this tenant.')
        return row

    def snapshot(self,row) -> dict:
        return self.read_schema.model_validate(row).model_dump(mode='json')

    def create(self,session: Session,actor: Actor,data):
        actor.require('write')
        values=self.normalized(data.model_dump())
        row=self.model(id=str(uuid4()),created_by=actor.user_id,**values)
        session.add(row);session.flush()
        record_event(session,actor,workspace=self.workspace,entity_id=row.id,action='create',revision=1,before=None,after=self.snapshot(row))
        emit_platform_event(session,actor,f'{self.workspace}.create',{'revision':1,'archived':False},entity_type=self.workspace,entity_id=row.id)
        return self.read_schema.model_validate(row)

    def change(self,session: Session,actor: Actor,row,expected: int,values: dict,action: str):
        if row.revision!=expected:
            raise AppError(409,'revision_conflict','This record changed. Review the current revision before saving.',{'current':self.snapshot(row)})
        before=self.snapshot(row)
        computed=self._computed_update(row,values)
        values={**values,**computed}
        result=session.execute(update(self.model).where(self.model.id==row.id,self.model.revision==expected).values(**values,revision=expected+1,updated_at=utcnow()),execution_options={'synchronize_session':False})
        if result.rowcount!=1:
            raise AppError(409,'revision_conflict','This record changed. Refresh before retrying.')
        session.refresh(row)
        record_event(session,actor,workspace=self.workspace,entity_id=row.id,action=action,revision=row.revision,before=before,after=self.snapshot(row))
        emit_platform_event(session,actor,f'{self.workspace}.{action}',{'revision':row.revision,'archived':bool(getattr(row,'archived',False))},entity_type=self.workspace,entity_id=row.id)
        return self.read_schema.model_validate(row)

    def update(self,session: Session,actor: Actor,record_id: str,expected: int,values: dict):
        actor.require('write')
        row=self.require(session,record_id)
        if row.archived:
            raise AppError(409,'archived_readonly','Restore this record before editing it.')
        return self.change(session,actor,row,expected,self.normalized(values),'update')

    def lifecycle(self,session: Session,actor: Actor,record_id: str,expected: int,action: str):
        actor.require('restore' if action=='restore' else 'write')
        if action not in ('archive','restore'):
            raise AppError(422,'invalid_action','Unsupported lifecycle action.')
        row=self.require(session,record_id);target=action=='archive'
        if row.archived==target:
            raise AppError(409,'invalid_transition','This record is already in the requested state.')
        return self.change(session,actor,row,expected,{'archived':target},action)


    def bulk_update(self, session: Session, actor: Actor, targets, patch: dict):
        actor.require('write')
        if not targets:
            raise AppError(422,'bulk_empty','Bulk update requires at least one record.')
        if len({target.id for target in targets}) != len(targets):
            raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
        allowed=set(self.create_schema.model_fields)
        unknown=set(patch)-allowed
        if unknown:
            raise AppError(422,'bulk_field_invalid','Bulk update contains an unsupported field.',{'fields':sorted(unknown)})
        prepared=[]
        for target in targets:
            row=self.require(session,target.id)
            if row.archived:
                raise AppError(409,'archived_readonly','Restore archived records before bulk editing.')
            if row.revision!=target.revision:
                raise AppError(409,'revision_conflict','A selected record changed. No records were modified.',{'current':self.snapshot(row),'record_id':row.id})
            current={field:getattr(row,field) for field in self.create_schema.model_fields}
            merged={**current,**patch}
            try:
                validated=self.create_schema.model_validate(merged)
            except ValueError as error:
                raise AppError(422,'bulk_validation','Bulk update failed field validation.',{'record_id':row.id,'message':str(error)[:500]}) from error
            prepared.append((row,target.revision,self.normalized(validated.model_dump())))
        # Validate every target before the first write. The surrounding transaction
        # provides rollback if a later database constraint still fails.
        return [self.change(session,actor,row,revision,values,'bulk_update') for row,revision,values in prepared]

    def history(self,session: Session,actor: Actor,record_id: str):
        actor.require('read');self.require(session,record_id)
        return list(session.scalars(select(AuditEvent).where(AuditEvent.workspace==self.workspace,AuditEvent.entity_id==record_id).order_by(AuditEvent.revision.desc()).limit(200)).all())

    def revert(self,session: Session,actor: Actor,record_id: str,current_revision: int,target_revision: int):
        actor.require('restore');row=self.require(session,record_id)
        if row.archived:
            raise AppError(409,'archived_readonly','Restore the record before reverting its contents.')
        event=session.scalar(select(AuditEvent).where(AuditEvent.workspace==self.workspace,AuditEvent.entity_id==record_id,AuditEvent.revision==target_revision))
        if not event or not event.after:
            raise AppError(404,'version_missing','Requested version is unavailable.')
        data=self.create_schema.model_validate({key:event.after[key] for key in self.create_schema.model_fields})
        return self.change(session,actor,row,current_revision,self.normalized(data.model_dump()),'revert')
