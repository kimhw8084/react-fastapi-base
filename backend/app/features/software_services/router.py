from typing import Annotated
from fastapi import APIRouter,Depends,Header,Query,Request
from app.platform.idempotency import execute_once
from app.platform.schemas import AuditRead,RevisionInput
from app.platform.security import Actor,actor_for
from app.platform.transactions import write_transaction
from . import service
from .schemas import SoftwareServiceCreate,SoftwareServiceUpdate,SoftwareServiceRead,SoftwareServicePage,SoftwareServiceBulkRequest,RevertRequest
router=APIRouter(prefix='/software-services',tags=['Software services']);A=Annotated[Actor,Depends(actor_for)]
@router.get('',response_model=SoftwareServicePage)
def list_records(request:Request,actor:A,search:str=Query('',max_length=200),archived:bool=False,sort:str='updated_at',direction:str='desc',limit:int=Query(50,ge=1,le=1000),offset:int=Query(0,ge=0),status:str='',tier:str='',environment:str=''):
    with request.app.state.database.session(actor.tenant_id) as db:return service.list_records(db,actor,search=search,filters={'status':status,'tier':tier,'environment':environment},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
@router.post('',response_model=SoftwareServiceRead,status_code=201)
def create(request:Request,actor:A,data:SoftwareServiceCreate,idempotency_key:str|None=Header(None)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return execute_once(db,actor,idempotency_key,'software_services.create',data.model_dump(),lambda:service.CRUD.create(db,actor,data).model_dump(mode='json'))
@router.post('/bulk',response_model=list[SoftwareServiceRead])
def bulk(request:Request,actor:A,data:SoftwareServiceBulkRequest,idempotency_key:str=Header(...)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        result=execute_once(db,actor,idempotency_key,'software_services.bulk',data.model_dump(),lambda:{'items':[row.model_dump(mode='json') for row in service.bulk(db,actor,data)]});return result['items']
@router.get('/{record_id}',response_model=SoftwareServiceRead)
def get_record(request:Request,actor:A,record_id:str):
    actor.require('read')
    with request.app.state.database.session(actor.tenant_id) as db:return SoftwareServiceRead.model_validate(service.CRUD.require(db,record_id))
@router.put('/{record_id}',response_model=SoftwareServiceRead)
def update_record(request:Request,actor:A,record_id:str,data:SoftwareServiceUpdate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.update(db,actor,record_id,data.revision,data.model_dump(exclude={'revision'}))
@router.post('/{record_id}/lifecycle/{action}',response_model=SoftwareServiceRead)
def lifecycle(request:Request,actor:A,record_id:str,action:str,data:RevisionInput):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.lifecycle(db,actor,record_id,data.revision,action)
@router.get('/{record_id}/history',response_model=list[AuditRead])
def history(request:Request,actor:A,record_id:str):
    with request.app.state.database.session(actor.tenant_id) as db:return service.CRUD.history(db,actor,record_id)
@router.post('/{record_id}/revert',response_model=SoftwareServiceRead)
def revert(request:Request,actor:A,record_id:str,data:RevertRequest):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.revert(db,actor,record_id,data.revision,data.target_revision)
