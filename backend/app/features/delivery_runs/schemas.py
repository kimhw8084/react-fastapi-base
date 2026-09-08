from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class DeliveryRunCreate(StrictSchema):
    run_id: str=Field(min_length=1,max_length=120)
    status: Literal['queued','running','passed','failed','cancelled']=Field(default='queued',max_length=80)
    environment: Literal['development','test','staging','production']=Field(default='staging',max_length=80)
    commit_sha: str | None=Field(default=None,max_length=80)
    branch: str | None=Field(default=None,max_length=160)
    started_at: datetime=Field()
    completed_at: datetime | None=Field(default=None)
    duration_minutes: float=Field(default=0.0,ge=0)
    stages: dict[str,Any]=Field(default={})
    artifacts: dict[str,Any]=Field(default={})
    triggered_by: str | None=Field(default=None,max_length=160)
    @field_validator('stages')
    @classmethod
    def validate_stages_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('artifacts')
    @classmethod
    def validate_artifacts_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class DeliveryRunUpdate(DeliveryRunCreate):
    revision:int=Field(ge=1)
class DeliveryRunRead(DeliveryRunCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class DeliveryRunPage(StrictSchema):
    items:list[DeliveryRunRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class DeliveryRunBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
