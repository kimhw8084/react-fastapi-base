from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class ObservabilityEventCreate(StrictSchema):
    event_id: str=Field(min_length=1,max_length=160)
    signal: Literal['log','trace','metric']=Field(default='log',max_length=80)
    severity: Literal['debug','info','warning','error','critical']=Field(default='info',max_length=80)
    timestamp: datetime=Field()
    duration_ms: float | None=Field(default=None,ge=0)
    trace_id: str | None=Field(default=None,max_length=160)
    span_id: str | None=Field(default=None,max_length=160)
    parent_span_id: str | None=Field(default=None,max_length=160)
    operation: str | None=Field(default=None,max_length=200)
    message: str | None=Field(default=None,max_length=30000)
    attributes: dict[str,Any]=Field(default={})
    @field_validator('attributes')
    @classmethod
    def validate_attributes_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class ObservabilityEventUpdate(ObservabilityEventCreate):
    revision:int=Field(ge=1)
class ObservabilityEventRead(ObservabilityEventCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class ObservabilityEventPage(StrictSchema):
    items:list[ObservabilityEventRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class ObservabilityEventBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
