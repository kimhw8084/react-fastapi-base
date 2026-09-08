from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class PlanTaskCreate(StrictSchema):
    title: str=Field(min_length=1,max_length=200)
    status: Literal['planned','ready','in_progress','blocked','done','cancelled']=Field(default='planned',max_length=80)
    start_date: date=Field()
    end_date: date=Field()
    baseline_start: date | None=Field(default=None)
    baseline_end: date | None=Field(default=None)
    progress: float=Field(default=0.0,ge=0,le=100)
    milestone: bool=Field(default=False)
    owner: str | None=Field(default=None,max_length=160)
    duration_days: int=Field(default=1,ge=1,le=3650)
    notes: str | None=Field(default=None,max_length=20000)
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class PlanTaskUpdate(PlanTaskCreate):
    revision:int=Field(ge=1)
class PlanTaskRead(PlanTaskCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class PlanTaskPage(StrictSchema):
    items:list[PlanTaskRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class PlanTaskBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
