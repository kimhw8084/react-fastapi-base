import base64
import binascii
import hashlib
from pathlib import PurePath
from uuid import uuid4
from typing import Protocol
from fastapi.responses import Response
from pydantic import Field
from sqlalchemy import select
from app.platform.schemas import StrictSchema, AttachmentRead
from app.platform.models import Attachment
from app.platform.errors import AppError
from app.platform.audit import record_event
from app.platform.security import Actor
from app.platform.storage import ObjectStorageAdapter

class MalwareScanner(Protocol):
    def scan(self, content: bytes, content_type: str, filename: str) -> bool: ...

class NoopMalwareScanner:
    """Development hook. Production may inject a malware/CDR adapter."""
    def scan(self, content: bytes, content_type: str, filename: str) -> bool:
        return True

class AttachmentUpload(StrictSchema):
    filename: str = Field(min_length=1,max_length=180)
    content_type: str
    content_base64: str = Field(max_length=1400000)

ALLOWED = {'text/plain','image/png','image/jpeg','application/pdf'}

def attach(session,actor: Actor,workspace: str,entity_id: str,data: AttachmentUpload, *, tenant_id: str|None=None, storage: ObjectStorageAdapter|None=None, scanner: MalwareScanner|None=None) -> AttachmentRead:
    actor.require('write')
    name=data.filename
    if '/' in name or '\\' in name or any(ord(c)<32 for c in name) or name in ('.','..'):
        raise AppError(422,'unsafe_filename','Attachment filename is invalid.')
    if data.content_type not in ALLOWED:
        raise AppError(422,'unsafe_file_type','This attachment type is not supported.')
    try:
        content=base64.b64decode(data.content_base64,validate=True)
    except (ValueError,binascii.Error):
        raise AppError(422,'invalid_file','Attachment encoding is invalid.') from None
    if not 0<len(content)<=1_000_000:
        raise AppError(413,'file_too_large','Attachments must be between 1 byte and 1 MB.')
    if data.content_type=='text/plain':
        try: content.decode('utf-8')
        except UnicodeDecodeError: raise AppError(422,'invalid_file','Text attachments must use UTF-8.') from None
    else:
        magic={'image/png':b'\x89PNG\r\n\x1a\n','image/jpeg':b'\xff\xd8\xff','application/pdf':b'%PDF-'}
        if not content.startswith(magic[data.content_type]):
            raise AppError(422,'invalid_file','The file signature does not match its media type.')
    if scanner is not None and not scanner.scan(content,data.content_type,name):
        raise AppError(422,'malware_rejected','The attachment was rejected by the configured content scanner.')
    attachment_id=str(uuid4())
    object_key=None
    stored_content=content
    if storage is not None:
        if not tenant_id:
            raise AppError(500,'storage_configuration','Attachment storage is missing a tenant boundary.')
        object_key=f'attachments/{attachment_id}/{name}'
        try:
            storage.put(tenant_id,object_key,content,data.content_type)
        except (OSError,ValueError):
            raise AppError(503,'storage_unavailable','The attachment storage is unavailable.') from None
        # Keep the database row small while preserving legacy inline rows.
        stored_content=b''
    row=Attachment(id=attachment_id,workspace=workspace,entity_id=entity_id,filename=name,
        content_type=data.content_type,size=len(content),sha256=hashlib.sha256(content).hexdigest(),
        content=stored_content,object_key=object_key,created_by=actor.user_id)
    session.add(row);session.flush()
    result=AttachmentRead.model_validate(row)
    record_event(session,actor,workspace='attachments',entity_id=row.id,action='upload',revision=1,before=None,after=result.model_dump(mode='json'))
    return result
