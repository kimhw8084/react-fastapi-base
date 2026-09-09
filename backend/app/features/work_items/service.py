from __future__ import annotations
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.models import AuditEvent
from app.platform.revision_service import RevisionCrudService
from app.platform.security import Actor
from .models import WorkItem
from .schemas import WorkItemCreate, WorkItemRead, WorkItemUpdate, WorkItemPage, BulkRequest

WORKSPACE='work_items'
SORTS={'title':WorkItem.title,'status':WorkItem.status,'priority':WorkItem.priority,'updated_at':WorkItem.updated_at,'created_at':WorkItem.created_at,'created_by':WorkItem.created_by,'revision':WorkItem.revision}
CRUD=RevisionCrudService(model=WorkItem,create_schema=WorkItemCreate,read_schema=WorkItemRead,workspace=WORKSPACE,not_found_label='Work item')

def require_item(session:Session,item_id:str)->WorkItem:return CRUD.require(session,item_id)
def snapshot(item:WorkItem)->dict:return CRUD.snapshot(item)

QUERY=EntityQueryService(model=WorkItem,read_schema=WorkItemRead,sorts=SORTS,search_columns=(WorkItem.title,WorkItem.description),filters={'status':(WorkItem.status,('open','in_progress','done')),'priority':(WorkItem.priority,('low','normal','high'))})

def list_items(session: Session, actor: Actor, *, search: str='', status: str='', priority: str='',archived: bool=False, sort: str='updated_at', direction: str='desc',limit: int=50, offset: int=0, sorts=None, advanced_filters=None) -> WorkItemPage:
    return QUERY.list(session,actor,page_schema=WorkItemPage,search=search,filter_values={'status':status,'priority':priority},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset,sorts=sorts,advanced_filters=advanced_filters)

def create_item(session:Session,actor:Actor,data:WorkItemCreate)->WorkItemRead:return CRUD.create(session,actor,data)
def update_item(session:Session,actor:Actor,item_id:str,data:WorkItemUpdate)->WorkItemRead:return CRUD.update(session,actor,item_id,data.revision,data.model_dump(exclude={'revision'}))
def change_item(session:Session,actor:Actor,item:WorkItem,expected:int,values:dict,action:str)->WorkItemRead:return CRUD.change(session,actor,item,expected,values,action)
def lifecycle(session:Session,actor:Actor,item_id:str,expected:int,action:str)->WorkItemRead:return CRUD.lifecycle(session,actor,item_id,expected,action)

def bulk_lifecycle(session:Session,actor:Actor,data:BulkRequest)->list[WorkItemRead]:
    if len({target.id for target in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate items.')
    return [CRUD.lifecycle(session,actor,target.id,target.revision,data.action) for target in data.targets]

def history(session:Session,actor:Actor,item_id:str)->list[AuditEvent]:return CRUD.history(session,actor,item_id)
def revert(session:Session,actor:Actor,item_id:str,current_revision:int,target_revision:int)->WorkItemRead:return CRUD.revert(session,actor,item_id,current_revision,target_revision)
