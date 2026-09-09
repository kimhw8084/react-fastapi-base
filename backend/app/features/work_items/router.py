from __future__ import annotations
import base64
import binascii
from typing import Annotated
from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import Response
from pydantic import Field
from sqlalchemy import select
from app.platform.errors import AppError
from app.platform.security import Actor, actor_for
from app.platform.schemas import AuditRead, RevisionInput, StrictSchema, AttachmentRead
from app.platform.transactions import write_transaction
from app.platform.idempotency import execute_once
from app.platform.models import Attachment
from app.platform.attachments import AttachmentUpload, attach
from . import service
from app.platform.query_service import decode_query_list
from .schemas import WorkItemCreate, WorkItemUpdate, WorkItemRead, WorkItemPage, BulkRequest, ImportPreviewRequest, ImportPreview, ImportCommit
from .exchange import export_csv, export_xlsx, preview_csv, preview_xlsx

router=APIRouter(prefix='/work-items',tags=['Work items'])
A=Annotated[Actor,Depends(actor_for)]

@router.get('',response_model=WorkItemPage,operation_id='listWorkItems')
def list_work_items(request: Request,actor: A, search: str=Query('',max_length=200),status: str='',priority: str='',archived: bool=False,sort: str='updated_at',direction: str='desc',sorts: str='',advanced_filters: str='',limit: int=Query(50,ge=1,le=1000),offset: int=Query(0,ge=0)):
    with request.app.state.database.session(actor.tenant_id) as db:
        return service.list_items(db,actor,search=search,status=status,priority=priority,archived=archived,sort=sort,direction=direction,sorts=decode_query_list(sorts,name='sorts',limit=8),advanced_filters=decode_query_list(advanced_filters,name='advanced_filters',limit=20),limit=limit,offset=offset)

@router.post('',response_model=WorkItemRead,status_code=201,operation_id='createWorkItem')
def create(request: Request,actor: A,data: WorkItemCreate,idempotency_key: str|None=Header(None)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return execute_once(db,actor,idempotency_key,'work_items.create',data.model_dump(),lambda:service.create_item(db,actor,data).model_dump(mode='json'))

@router.post('/bulk',response_model=list[WorkItemRead],operation_id='bulkWorkItems')
def bulk(request: Request,actor: A,data: BulkRequest,idempotency_key: str=Header(...)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        result=execute_once(db,actor,idempotency_key,'work_items.bulk',data.model_dump(),lambda:{'items':[row.model_dump(mode='json') for row in service.bulk_lifecycle(db,actor,data)]})
        return result['items']

@router.get('/export.csv',operation_id='exportWorkItems')
def export(request: Request,actor: A, search: str=Query('',max_length=200),status: str='',priority: str='',archived: bool=False):
    actor.require('export')
    with request.app.state.database.session(actor.tenant_id) as db:
        result=service.list_items(db,actor,search=search,status=status,priority=priority,archived=archived,limit=1000)
        if result.total>1000:
            raise AppError(413,'export_too_large','Narrow the filters to at most 1000 records.')
        return Response(export_csv(result.items),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="work-items-v1.csv"','X-Content-Type-Options':'nosniff'})

@router.get('/export.xlsx',operation_id='exportWorkItemsXlsx')
def export_xlsx_file(request: Request,actor: A, search: str=Query('',max_length=200),status: str='',priority: str='',archived: bool=False):
    actor.require('export')
    with request.app.state.database.session(actor.tenant_id) as db:
        result=service.list_items(db,actor,search=search,status=status,priority=priority,archived=archived,limit=1000)
        if result.total>1000:raise AppError(413,'export_too_large','Narrow the filters to at most 1000 records.')
        return Response(export_xlsx(result.items),media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename="work-items-v1.xlsx"','X-Content-Type-Options':'nosniff'})

def _preview_exchange(data: ImportPreviewRequest):
    if data.csv is not None:return preview_csv(data.csv)
    try:content=base64.b64decode(data.xlsx_base64 or '',validate=True)
    except (ValueError,binascii.Error):raise AppError(422,'invalid_file','XLSX encoding is invalid.') from None
    return preview_xlsx(content)

@router.post('/import/preview',response_model=ImportPreview,operation_id='previewWorkItemImport')
def preview(request: Request,actor: A,data: ImportPreviewRequest):
    actor.require('import')
    return _preview_exchange(data)

@router.post('/import/commit',response_model=list[WorkItemRead],operation_id='commitWorkItemImport')
def commit_import(request: Request,actor: A,data: ImportCommit,idempotency_key: str=Header(...)):
    actor.require('import')
    if data.csv is not None:preview=preview_csv(data.csv)
    else:
        try:content=base64.b64decode(data.xlsx_base64 or '',validate=True)
        except (ValueError,binascii.Error):raise AppError(422,'invalid_file','XLSX encoding is invalid.') from None
        preview=preview_xlsx(content)
    if preview.errors or preview.fingerprint!=data.fingerprint or not preview.rows:
        raise AppError(422,'import_review_required','Correct errors and review a fresh preview before importing.',{'errors':preview.errors})
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        result=execute_once(db,actor,idempotency_key,'work_items.import',{'fingerprint':preview.fingerprint},lambda:{'items':[service.create_item(db,actor,row).model_dump(mode='json') for row in preview.rows]})
        return result['items']

@router.get('/{item_id}',response_model=WorkItemRead,operation_id='getWorkItem')
def get(request: Request,actor: A,item_id: str):
    with request.app.state.database.session(actor.tenant_id) as db:
        return WorkItemRead.model_validate(service.require_item(db,item_id))

@router.put('/{item_id}',response_model=WorkItemRead,operation_id='updateWorkItem')
def update(request: Request,actor: A,item_id: str,data: WorkItemUpdate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return service.update_item(db,actor,item_id,data)

@router.post('/{item_id}/lifecycle/{action}',response_model=WorkItemRead,operation_id='transitionWorkItem')
def lifecycle(request: Request,actor: A,item_id: str,action: str,data: RevisionInput):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return service.lifecycle(db,actor,item_id,data.revision,action)

@router.get('/{item_id}/history',response_model=list[AuditRead],operation_id='workItemHistory')
def history(request: Request,actor: A,item_id: str):
    with request.app.state.database.session(actor.tenant_id) as db:
        return [AuditRead.model_validate(row) for row in service.history(db,actor,item_id)]

class RevertInput(RevisionInput):
    target_revision: int = Field(ge=1)

@router.post('/{item_id}/revert',response_model=WorkItemRead,operation_id='revertWorkItem')
def revert(request: Request,actor: A,item_id: str,data: RevertInput):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return service.revert(db,actor,item_id,data.revision,data.target_revision)

@router.get('/{item_id}/attachments',response_model=list[AttachmentRead],operation_id='listAttachments')
def attachments(request: Request,actor: A,item_id: str):
    with request.app.state.database.session(actor.tenant_id) as db:
        service.require_item(db,item_id)
        return [AttachmentRead.model_validate(row) for row in db.scalars(select(Attachment).where(Attachment.entity_id==item_id,Attachment.workspace=='work_items')).all()]

@router.post('/{item_id}/attachments',response_model=AttachmentRead,status_code=201,operation_id='addAttachment')
def add_attachment(request: Request,actor: A,item_id: str,data: AttachmentUpload):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        item=service.require_item(db,item_id)
        if item.archived:
            raise AppError(409,'archived_readonly','Restore the item before adding files.')
        return attach(db,actor,'work_items',item_id,data,tenant_id=actor.tenant_id,storage=request.app.state.object_storage,scanner=request.app.state.malware_scanner)

@router.get('/{item_id}/attachments/{attachment_id}',operation_id='downloadAttachment')
def download_attachment(request: Request,actor: A,item_id: str,attachment_id: str):
    from urllib.parse import quote
    with request.app.state.database.session(actor.tenant_id) as db:
        service.require_item(db,item_id)
        row=db.get(Attachment,attachment_id)
        if row is None or row.entity_id!=item_id or row.workspace!='work_items':
            raise AppError(404,'attachment_missing','Attachment is not available.')
        try:
            content=request.app.state.object_storage.get(actor.tenant_id,row.object_key) if row.object_key else row.content
        except (FileNotFoundError,ValueError,OSError):
            raise AppError(503,'storage_unavailable','The attachment storage is unavailable.') from None
        return Response(content,media_type='application/octet-stream',headers={'Content-Disposition':f"attachment; filename*=UTF-8''{quote(row.filename,safe='')}",'X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; sandbox"})
