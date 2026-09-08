from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class IncidentCreate(StrictSchema):
    incident_number: str=Field(min_length=1,max_length=80)
    title: str=Field(min_length=1,max_length=240)
    status: Literal['investigating','identified','monitoring','resolved','closed']=Field(default='investigating',max_length=80)
    severity: Literal['sev_1','sev_2','sev_3','sev_4']=Field(default='sev_3',max_length=80)
    started_at: datetime=Field()
    resolved_at: datetime | None=Field(default=None)
    duration_minutes: float=Field(default=0.0,ge=0)
    commander: str | None=Field(default=None,max_length=160)
    impact: str | None=Field(default=None,max_length=50000)
    timeline: dict[str,Any]=Field(default={})
    actions: dict[str,Any]=Field(default={})
    @field_validator('timeline')
    @classmethod
    def validate_timeline_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('actions')
    @classmethod
    def validate_actions_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class IncidentUpdate(IncidentCreate):
    revision:int=Field(ge=1)
class IncidentRead(IncidentCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class IncidentPage(StrictSchema):
    items:list[IncidentRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class IncidentBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
