from typing import Annotated
from fastapi import APIRouter,Depends,Header,Query,Request
from app.platform.idempotency import execute_once
from app.platform.schemas import AuditRead,RevisionInput
from app.platform.security import Actor,actor_for
from app.platform.transactions import write_transaction
from . import service
from .schemas import ProjectCreate,ProjectUpdate,ProjectRead,ProjectPage,ProjectBulkRequest,RevertRequest
router=APIRouter(prefix='/projects',tags=['Projects']);A=Annotated[Actor,Depends(actor_for)]

@router.get('',response_model=ProjectPage,operation_id='listProjects')
def list_projects(request:Request,actor:A,search:str=Query('',max_length=200),status:str='',archived:bool=False,sort:str='updated_at',direction:str='desc',limit:int=Query(50,ge=1,le=1000),offset:int=Query(0,ge=0)):
    with request.app.state.database.session(actor.tenant_id) as db:return service.list_projects(db,actor,search=search,status=status,archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
@router.post('',response_model=ProjectRead,status_code=201,operation_id='createProject')
def create(request:Request,actor:A,data:ProjectCreate,idempotency_key:str|None=Header(None)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return execute_once(db,actor,idempotency_key,'projects.create',data.model_dump(),lambda:service.CRUD.create(db,actor,data).model_dump(mode='json'))
@router.post('/bulk',response_model=list[ProjectRead],operation_id='bulkProjects')
def bulk(request:Request,actor:A,data:ProjectBulkRequest,idempotency_key:str=Header(...)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        result=execute_once(db,actor,idempotency_key,'projects.bulk',data.model_dump(),lambda:{'items':[row.model_dump(mode='json') for row in service.bulk(db,actor,data)]});return result['items']
@router.get('/{project_id}',response_model=ProjectRead,operation_id='getProject')
def get_project(request:Request,actor:A,project_id:str):
    actor.require('read')
    with request.app.state.database.session(actor.tenant_id) as db:return ProjectRead.model_validate(service.CRUD.require(db,project_id))
@router.put('/{project_id}',response_model=ProjectRead,operation_id='updateProject')
def update_project(request:Request,actor:A,project_id:str,data:ProjectUpdate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.update(db,actor,project_id,data.revision,data.model_dump(exclude={'revision'}))
@router.post('/{project_id}/lifecycle/{action}',response_model=ProjectRead,operation_id='projectLifecycle')
def lifecycle(request:Request,actor:A,project_id:str,action:str,data:RevisionInput):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.lifecycle(db,actor,project_id,data.revision,action)
@router.get('/{project_id}/history',response_model=list[AuditRead],operation_id='projectHistory')
def history(request:Request,actor:A,project_id:str):
    with request.app.state.database.session(actor.tenant_id) as db:return service.CRUD.history(db,actor,project_id)
@router.post('/{project_id}/revert',response_model=ProjectRead,operation_id='revertProject')
def revert(request:Request,actor:A,project_id:str,data:RevertRequest):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.revert(db,actor,project_id,data.revision,data.target_revision)
