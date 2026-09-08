from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class StrictSchema(BaseModel):
    model_config = ConfigDict(extra='forbid', from_attributes=True, json_schema_serialization_defaults_required=True)

    @field_validator('*', mode='after')
    @classmethod
    def explicit_utc(cls, value):
        # SQLite DateTime loses tzinfo; all persisted timestamps in this schema are UTC.
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

class ErrorBody(StrictSchema):
    code: str
    message: str
    request_id: str
    details: Any = None

class ErrorResponse(StrictSchema):
    error: ErrorBody

class TenantInfo(StrictSchema):
    id: str
    name: str
    role: str
    permissions: list[str]

from app.platform.configuration import ApplicationConfig

class Bootstrap(StrictSchema):
    user_id: str
    profile: str
    csrf_token: str
    tenants: list[TenantInfo]
    application: ApplicationConfig
    build_version: str

class FieldDefinition(StrictSchema):
    key: str
    label: str
    kind: Literal['text','textarea','select','integer','number','boolean','date','datetime','email','url','markdown','code','json','multiselect','percent','duration','scientific','unit_number']
    required: bool = False
    nullable: bool = False
    max_length: int | None = None
    choices: list[str] = Field(default_factory=list)
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    unit: str | None = Field(default=None, max_length=24)
    read_only: bool = False
    @model_validator(mode='after')
    def unit_contract(self):
        numeric={'integer','number','percent','duration','scientific','unit_number'}
        if self.unit is not None and self.kind not in numeric:
            raise ValueError('Units are only valid for numeric fields.')
        if self.kind == 'unit_number' and not self.unit:
            raise ValueError('unit_number fields require a unit.')
        return self

class WorkspaceDefinition(StrictSchema):
    key: str
    label: str
    description: str
    schema_version: int = 1
    fields: list[FieldDefinition]
    columns: list[str]
    capabilities: list[str]
    primary_field: str = "title"
    filter_keys: list[str] = Field(default_factory=list)
    sort_keys: list[str] = Field(default_factory=list)
    visualizations: list[str] = Field(default_factory=lambda: ['table'], min_length=1, max_length=20)

class EntityDefinition(StrictSchema):
    key: str = Field(pattern=r'^[a-z][a-z0-9_]{0,39}$')
    label: str = Field(min_length=1, max_length=120)
    description: str = Field(default='', max_length=500)
    workspace: str = Field(pattern=r'^[a-z][a-z0-9_]{0,39}$')
    primary_field: str = Field(default='title', min_length=1, max_length=60)
    authority: Literal['canonical','reference','derived','external','transient'] = 'canonical'
    search_fields: list[str] = Field(default_factory=list, max_length=20)
    capabilities: list[str] = Field(default_factory=list, max_length=40)

class EntityReference(StrictSchema):
    entity: str
    id: str
    label: str
    workspace: str
    archived: bool = False
    revision: int | None = None

class GlobalSearchResult(StrictSchema):
    kind: Literal['record', 'saved_view']
    id: str
    label: str
    description: str = ''
    entity: str | None = None
    workspace: str

class EntityBulkUpdateTarget(StrictSchema):
    id: str = Field(min_length=1, max_length=64)
    revision: int = Field(ge=1)

class EntityBulkUpdateRequest(StrictSchema):
    targets: list[EntityBulkUpdateTarget] = Field(min_length=1, max_length=100)
    patch: dict[str, Any] = Field(min_length=1, max_length=20)
    @field_validator('patch')
    @classmethod
    def safe_patch_keys(cls, value):
        if any(not isinstance(key,str) or not key or len(key)>60 for key in value):
            raise ValueError('Bulk patch contains an invalid field key.')
        return value

class EntityBulkUpdateResult(StrictSchema):
    updated: list[EntityReference]

class RelationshipDefinition(StrictSchema):
    key: str = Field(pattern=r'^[a-z][a-z0-9_]{0,59}$')
    label: str = Field(min_length=1, max_length=120)
    source_entity: str = Field(pattern=r'^[a-z][a-z0-9_]{0,39}$')
    target_entity: str = Field(pattern=r'^[a-z][a-z0-9_]{0,39}$')
    forward_label: str = Field(min_length=1, max_length=120)
    reverse_label: str = Field(min_length=1, max_length=120)
    cardinality: Literal['one_to_one','one_to_many','many_to_one','many_to_many'] = 'many_to_many'
    kind: Literal['reference','hierarchy','dependency','placement','causal','temporal','logical','connection'] = 'reference'
    placement_capacity: int | None = Field(default=None, ge=1, le=1000)
    allow_self: bool = False
    acyclic: bool = False
    allow_parallel: bool = False
    @model_validator(mode='after')
    def placement_contract(self):
        if self.kind == 'placement' and self.placement_capacity is None:
            raise ValueError('Placement relationships require placement_capacity.')
        if self.kind != 'placement' and self.placement_capacity is not None:
            raise ValueError('placement_capacity is only valid for placement relationships.')
        if self.kind == 'placement' and self.source_entity == self.target_entity:
            raise ValueError('Placement source and target entities must differ.')
        return self

class RelationshipCreate(StrictSchema):
    definition_key: str = Field(pattern=r'^[a-z][a-z0-9_]{0,59}$')
    source_id: str = Field(min_length=1, max_length=64)
    target_id: str = Field(min_length=1, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)

class RelationshipUpdate(StrictSchema):
    revision: int = Field(ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

class RelationshipRead(StrictSchema):
    id: str
    definition_key: str
    source: EntityReference
    target: EntityReference
    metadata: dict[str, Any]
    revision: int
    archived: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

class ViewColumn(StrictSchema):
    colId: str = Field(min_length=1, max_length=60)
    width: int = Field(default=160, ge=60, le=1200)
    hide: bool = False
    sort: Literal['asc','desc'] | None = None
    sortIndex: int | None = Field(default=None, ge=0, le=30)
    pinned: Literal['left','right'] | None = None

class ViewDefinition(StrictSchema):
    search: str = Field(default='', max_length=200)
    filters: dict[str, str] = Field(default_factory=dict, max_length=20)
    archived: bool = False
    group_by: str = Field(default='', max_length=40)
    sort: str = Field(default='updated_at', max_length=40)
    direction: Literal['asc', 'desc'] = 'desc'
    density: Literal['comfortable','compact'] = 'comfortable'
    visualization: str = Field(default='table', min_length=1, max_length=40)
    columns: list[ViewColumn] = Field(default_factory=list, max_length=30)

class ViewCreate(StrictSchema):
    name: str = Field(min_length=1, max_length=120)
    scope: Literal['personal','team'] = 'personal'
    definition: ViewDefinition
    @field_validator('name')
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Name cannot be blank.')
        return value

class ViewUpdate(ViewCreate):
    revision: int = Field(ge=1)

class ViewRead(ViewCreate):
    id: str
    workspace: str
    owner: str
    revision: int
    schema_version: int
    updated_at: datetime

class RevisionInput(StrictSchema):
    revision: int = Field(ge=1)

class AuditRead(StrictSchema):
    id: str
    actor: str
    workspace: str
    entity_id: str
    action: str
    revision: int
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    request_id: str
    created_at: datetime

class AttachmentRead(StrictSchema):
    id: str
    filename: str
    content_type: str
    size: int
    sha256: str
    created_by: str
    created_at: datetime

class JobCreate(StrictSchema):
    job_type: str = Field(pattern=r'^[a-z][a-z0-9_.-]{0,79}$')
    payload: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=3,ge=1,le=20)
    run_after: datetime | None = None
class JobRead(StrictSchema):
    id:str;job_type:str;status:str;payload:dict[str,Any];result:dict[str,Any]|None;error:str|None;attempts:int;max_attempts:int;run_after:datetime;lease_owner:str|None;lease_expires_at:datetime|None;created_by:str;created_at:datetime;updated_at:datetime
class EventRead(StrictSchema):
    sequence:int;event_id:str;topic:str;entity_type:str|None;entity_id:str|None;payload:dict[str,Any];created_by:str;created_at:datetime
class NotificationCreate(StrictSchema):
    user_id:str=Field(min_length=1,max_length=200);kind:str=Field(pattern=r'^[a-z][a-z0-9_.-]{0,59}$');title:str=Field(min_length=1,max_length=180);body:str=Field(default='',max_length=2000);data:dict[str,Any]=Field(default_factory=dict)
class NotificationRead(StrictSchema):
    id:str;user_id:str;kind:str;title:str;body:str;data:dict[str,Any];read_at:datetime|None;created_at:datetime
class NotificationPreferenceUpdate(StrictSchema):
    enabled:bool;revision:int|None=Field(default=None,ge=1)
class NotificationPreferenceRead(StrictSchema):
    user_id:str;kind:str;enabled:bool;revision:int;updated_at:datetime
class FeatureFlagWrite(StrictSchema):
    enabled:bool=False;description:str=Field(default='',max_length=300);rules:dict[str,Any]=Field(default_factory=dict,max_length=20);revision:int|None=Field(default=None,ge=1)
class FeatureFlagRead(StrictSchema):
    key:str;enabled:bool;description:str;rules:dict[str,Any];revision:int;updated_by:str;updated_at:datetime
class WebhookEndpointWrite(StrictSchema):
    name:str=Field(min_length=1,max_length=120);url:str=Field(min_length=1,max_length=500);topics:list[str]=Field(min_length=1,max_length=30);secret_ref:str=Field(pattern=r'^[A-Z][A-Z0-9_]{0,79}$');enabled:bool=True;revision:int|None=Field(default=None,ge=1)
    @field_validator('topics')
    @classmethod
    def safe_topics(cls,value):
        if len(set(value))!=len(value) or any(not isinstance(x,str) or len(x)>100 or not x or not all(c.isalnum() or c in '._-' for c in x) for x in value):raise ValueError('Webhook topics must be unique safe topic names.')
        return value
class WebhookEndpointRead(StrictSchema):
    id:str;name:str;url:str;topics:list[str];secret_ref:str;enabled:bool;revision:int;created_by:str;created_at:datetime;updated_at:datetime

class MemberWrite(StrictSchema):
    user_id:str=Field(min_length=1,max_length=200)
    role:str=Field(min_length=1,max_length=40)
class MemberRead(StrictSchema):
    user_id:str;role:str
class PermissionMatrixRead(StrictSchema):
    roles:dict[str,list[str]]
