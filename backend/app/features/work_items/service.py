from __future__ import annotations
import hashlib
import json
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.models import AuditEvent
from app.platform.revision_service import RevisionCrudService
from app.platform.security import Actor
from .models import WorkItem
from .schemas import WorkItemCreate, WorkItemRead, WorkItemUpdate, WorkItemPage, BulkRequest, MatchingBulkRequest, MatchingBulkPreview

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

def matching_bulk_rows(session:Session,actor:Actor,view) -> list[WorkItemRead]:
    filters=view.filters
    kwargs={'search':view.search,'status':filters.get('status',''),'priority':filters.get('priority',''),'archived':view.archived,'sort':view.sort,'direction':view.direction,'sorts':[item.model_dump() for item in view.sorts],'advanced_filters':view.advanced_filters}
    page=list_items(session,actor,**kwargs,limit=1000,offset=0)
    if page.total>10000:
        raise AppError(413,'bulk_scope_too_large','All-matching bulk operations are limited to 10,000 records. Narrow the query first.')
    rows=list(page.items)
    while len(rows)<page.total:
        next_page=list_items(session,actor,**kwargs,limit=1000,offset=len(rows))
        rows.extend(next_page.items)
    return rows

def matching_bulk_fingerprint(rows:list[WorkItemRead])->str:
    payload=[{'id':row.id,'revision':row.revision} for row in rows]
    return hashlib.sha256(json.dumps(payload,separators=(',',':'),sort_keys=True).encode()).hexdigest()

def preview_matching_bulk(session:Session,actor:Actor,view)->MatchingBulkPreview:
    rows=matching_bulk_rows(session,actor,view)
    return MatchingBulkPreview(total=len(rows),fingerprint=matching_bulk_fingerprint(rows),sample=rows[:20])

def bulk_matching(session:Session,actor:Actor,data:MatchingBulkRequest)->list[WorkItemRead]:
    rows=matching_bulk_rows(session,actor,data.view)
    fingerprint=matching_bulk_fingerprint(rows)
    if len(rows)!=data.expected_total or fingerprint!=data.fingerprint:
        raise AppError(409,'bulk_scope_changed','The matching query changed. Refresh the preview before applying it.',{'current_total':len(rows),'current_fingerprint':fingerprint})
    return [CRUD.lifecycle(session,actor,row.id,row.revision,data.action) for row in rows]

def history(session:Session,actor:Actor,item_id:str)->list[AuditEvent]:return CRUD.history(session,actor,item_id)
def revert(session:Session,actor:Actor,item_id:str,current_revision:int,target_revision:int)->WorkItemRead:return CRUD.revert(session,actor,item_id,current_revision,target_revision)
