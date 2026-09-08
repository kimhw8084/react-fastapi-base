from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class EquipmentStateCreate(StrictSchema):
    label: str=Field(min_length=1,max_length=160)
    state: Literal['production','standby','engineering','scheduled_down','unscheduled_down']=Field(min_length=1,max_length=80)
    module: str | None=Field(default=None,max_length=120)
    started_at: datetime=Field()
    ended_at: datetime | None=Field(default=None)
    duration_minutes: float=Field(default=0.0,ge=0)
    reason: str | None=Field(default=None,max_length=10000)
    alarm_code: str | None=Field(default=None,max_length=80)
    context: dict[str,Any]=Field(default={})
    @field_validator('context')
    @classmethod
    def validate_context_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class EquipmentStateUpdate(EquipmentStateCreate):
    revision:int=Field(ge=1)
class EquipmentStateRead(EquipmentStateCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class EquipmentStatePage(StrictSchema):
    items:list[EquipmentStateRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class EquipmentStateBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
