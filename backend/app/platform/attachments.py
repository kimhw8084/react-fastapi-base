import base64
import binascii
import hashlib
from uuid import uuid4
from typing import Literal, Protocol
from pydantic import Field
from app.platform.schemas import StrictSchema, AttachmentRead
from app.platform.models import Attachment
from app.platform.errors import AppError
from app.platform.audit import record_event
from app.platform.security import Actor
from app.platform.storage import ObjectStorageAdapter, validate_content_type
from app.platform.entity_registry import EntityRegistry

class MalwareScanner(Protocol):
    def scan(self, content: bytes, content_type: str, filename: str) -> bool: ...


class DeterministicMalwareScanner:
    """Local contract-test scanner.

    It is deliberately conservative and deterministic: it rejects the standard
    EICAR test token and active SVG content. Production deployments replace it
    with a malware/CDR adapter before enabling unrestricted document uploads.
    """

    EICAR_TOKEN = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

    def scan(self, content: bytes, content_type: str, filename: str) -> bool:
        if self.EICAR_TOKEN in content:
            return False
        if content_type == 'image/svg+xml' or filename.casefold().endswith('.svg'):
            return False
        return True

class NoopMalwareScanner:
    """Explicit no-op adapter; it provides no malware protection.

    It is acceptable only for the bounded ``trusted_types`` policy and local
    compatibility tests. ``scanner_required`` rejects it in this service, so
    production cannot accidentally present it as malware scanning.
    """
    def scan(self, content: bytes, content_type: str, filename: str) -> bool:
        return True

class AttachmentUpload(StrictSchema):
    filename: str = Field(min_length=1,max_length=180)
    content_type: str
    content_base64: str = Field(max_length=1400000)

ALLOWED = {'text/plain','image/png','image/jpeg','application/pdf'}
AttachmentUploadMode = Literal['disabled', 'trusted_types', 'scanner_required']

def _validate_upload_boundary(actor: Actor, tenant_id: str, upload_mode: str) -> None:
    if upload_mode not in {'disabled', 'trusted_types', 'scanner_required'}:
        raise AppError(500, 'attachment_policy_invalid', 'The attachment upload policy is invalid.')
    if tenant_id != actor.tenant_id:
        raise AppError(403, 'tenant_forbidden', 'Attachment storage must use the authenticated tenant.')
    try:
        from uuid import UUID
        if str(UUID(tenant_id)) != tenant_id:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise AppError(500, 'storage_configuration', 'Attachment storage has an invalid tenant boundary.') from None


def attach(session,actor: Actor,workspace: str,entity_id: str,data: AttachmentUpload, *, tenant_id: str, storage: ObjectStorageAdapter, scanner: MalwareScanner|None, upload_mode: AttachmentUploadMode, registry: EntityRegistry) -> AttachmentRead:
    actor.require('write')
    _validate_upload_boundary(actor, tenant_id, upload_mode)
    if upload_mode == 'disabled':
        raise AppError(503, 'attachments_disabled', 'Attachment uploads are disabled by deployment policy.')
    if upload_mode == 'scanner_required' and (scanner is None or isinstance(scanner, NoopMalwareScanner)):
        raise AppError(503, 'scanner_unavailable', 'The attachment scanner is unavailable.')
    reference = registry.resolve(session, workspace, entity_id)
    if reference.archived:
        raise AppError(409, 'archived_readonly', 'Archived records are read-only, including attachments.')
    name=data.filename
    if '/' in name or '\\' in name or any(ord(c)<32 for c in name) or name in ('.','..'):
        raise AppError(422,'unsafe_filename','Attachment filename is invalid.')
    if data.content_type not in ALLOWED:
        raise AppError(422,'unsafe_file_type','This attachment type is not supported.')
    validate_content_type(data.content_type)
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
    if upload_mode == 'scanner_required':
        try:
            assert scanner is not None
            accepted = scanner.scan(content,data.content_type,name)
        except Exception:
            raise AppError(503,'scanner_unavailable','The attachment scanner is unavailable.') from None
        if accepted is not True:
            if not isinstance(accepted, bool):
                raise AppError(503,'scanner_unavailable','The attachment scanner returned an invalid result.')
            raise AppError(422,'malware_rejected','The attachment was rejected by the configured content scanner.')
    attachment_id=str(uuid4())
    object_key=None
    stored_content=content
    object_key=f'attachments/{attachment_id}/{name}'
    expected_digest=hashlib.sha256(content).hexdigest()
    try:
        stored=storage.put(tenant_id,object_key,content,data.content_type)
        if (stored.key != object_key or stored.size != len(content) or stored.sha256 != expected_digest or stored.content_type != data.content_type):
            raise ValueError('Object storage returned inconsistent metadata.')
    except Exception:
        try:
            storage.delete(tenant_id, object_key)
        except Exception:
            pass
        raise AppError(503,'storage_unavailable','The attachment storage is unavailable.') from None
    # Keep the database row small while preserving legacy inline rows.
    stored_content=b''
    row=Attachment(id=attachment_id,workspace=workspace,entity_id=entity_id,filename=name,
        content_type=data.content_type,size=len(content),sha256=expected_digest,
        content=stored_content,object_key=object_key,created_by=actor.user_id)
    try:
        session.add(row);session.flush()
    except Exception:
        if object_key is not None:
            try:
                storage.delete(tenant_id, object_key)
            except Exception:
                pass
        raise
    result=AttachmentRead.model_validate(row)
    record_event(session,actor,workspace='attachments',entity_id=row.id,action='upload',revision=1,before=None,after=result.model_dump(mode='json'))
    return result


def read_content(row: Attachment, *, tenant_id: str, storage: ObjectStorageAdapter) -> bytes:
    """Return an attachment only when bytes still match canonical metadata."""
    try:
        content = storage.get(tenant_id, row.object_key) if row.object_key else row.content
    except Exception:
        raise AppError(503, 'storage_unavailable', 'The attachment storage is unavailable.') from None
    if not isinstance(content, bytes) or len(content) != row.size or hashlib.sha256(content).hexdigest() != row.sha256:
        raise AppError(503, 'storage_integrity', 'The attachment bytes failed integrity validation.')
    return content
