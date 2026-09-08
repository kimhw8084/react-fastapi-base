from typing import Annotated
from collections import defaultdict
from datetime import date
from sqlalchemy import select
from app.platform.errors import AppError
from .models import PlanTask
from fastapi import APIRouter,Depends,Header,Query,Request
from app.platform.idempotency import execute_once
from app.platform.schemas import AuditRead,RevisionInput
from app.platform.security import Actor,actor_for
from app.platform.transactions import write_transaction
from . import service
from .schemas import PlanTaskCreate,PlanTaskUpdate,PlanTaskRead,PlanTaskPage,PlanTaskBulkRequest,RevertRequest
router=APIRouter(prefix='/plan-tasks',tags=['Planning']);A=Annotated[Actor,Depends(actor_for)]
@router.get('',response_model=PlanTaskPage)
def list_records(request:Request,actor:A,search:str=Query('',max_length=200),archived:bool=False,sort:str='updated_at',direction:str='desc',limit:int=Query(50,ge=1,le=1000),offset:int=Query(0,ge=0),status:str='',milestone:str=''):
    with request.app.state.database.session(actor.tenant_id) as db:return service.list_records(db,actor,search=search,filters={'status':status,'milestone':milestone},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)

@router.get('/capacity',operation_id='planCapacity')
def capacity(request:Request,actor:A,start:date|None=None,end:date|None=None):
    actor.require('read')
    if start and end and end<start: raise AppError(422,'invalid_range','Capacity end cannot precede start.')
    with request.app.state.database.session(actor.tenant_id) as db:
        rows=db.scalars(select(PlanTask).where(PlanTask.archived.is_(False))).all()
    grouped=defaultdict(lambda:{'resource_group':'Unassigned','task_count':0,'effort_hours':0.0,'capacity_hours':0.0,'baseline_slip_days':0})
    for row in rows:
        if start and row.end_date<start: continue
        if end and row.start_date>end: continue
        key=row.resource_group or row.owner or 'Unassigned';entry=grouped[key];entry['resource_group']=key;entry['task_count']+=1;entry['effort_hours']+=row.effort_hours;entry['capacity_hours']+=row.capacity_hours
        if row.baseline_end and row.end_date>row.baseline_end: entry['baseline_slip_days']=max(entry['baseline_slip_days'],(row.end_date-row.baseline_end).days)
    return [dict(value,overallocated=value['effort_hours']>value['capacity_hours']) for value in sorted(grouped.values(),key=lambda item:item['resource_group'].lower())]
@router.post('',response_model=PlanTaskRead,status_code=201)
def create(request:Request,actor:A,data:PlanTaskCreate,idempotency_key:str|None=Header(None)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return execute_once(db,actor,idempotency_key,'plan_tasks.create',data.model_dump(),lambda:service.CRUD.create(db,actor,data).model_dump(mode='json'))
@router.post('/bulk',response_model=list[PlanTaskRead])
def bulk(request:Request,actor:A,data:PlanTaskBulkRequest,idempotency_key:str=Header(...)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        result=execute_once(db,actor,idempotency_key,'plan_tasks.bulk',data.model_dump(),lambda:{'items':[row.model_dump(mode='json') for row in service.bulk(db,actor,data)]});return result['items']
@router.get('/{record_id}',response_model=PlanTaskRead)
def get_record(request:Request,actor:A,record_id:str):
    actor.require('read')
    with request.app.state.database.session(actor.tenant_id) as db:return PlanTaskRead.model_validate(service.CRUD.require(db,record_id))
@router.put('/{record_id}',response_model=PlanTaskRead)
def update_record(request:Request,actor:A,record_id:str,data:PlanTaskUpdate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.update(db,actor,record_id,data.revision,data.model_dump(exclude={'revision'}))
@router.post('/{record_id}/lifecycle/{action}',response_model=PlanTaskRead)
def lifecycle(request:Request,actor:A,record_id:str,action:str,data:RevisionInput):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.lifecycle(db,actor,record_id,data.revision,action)
@router.get('/{record_id}/history',response_model=list[AuditRead])
def history(request:Request,actor:A,record_id:str):
    with request.app.state.database.session(actor.tenant_id) as db:return service.CRUD.history(db,actor,record_id)
@router.post('/{record_id}/revert',response_model=PlanTaskRead)
def revert(request:Request,actor:A,record_id:str,data:RevertRequest):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.revert(db,actor,record_id,data.revision,data.target_revision)
