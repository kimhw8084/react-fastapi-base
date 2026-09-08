from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class ServiceObjectiveCreate(StrictSchema):
    name: str=Field(min_length=1,max_length=200)
    window_days: int=Field(default=30,ge=1,le=365)
    target_percent: float=Field(default=99.9,ge=0.001,le=100)
    current_percent: float=Field(default=100.0,ge=0,le=100)
    error_budget_remaining: float=Field(default=100.0,ge=0,le=100)
    burn_rate: float=Field(default=0.0,ge=0)
    status: Literal['healthy','warning','exhausted']=Field(default='healthy',max_length=80)
    notes: str | None=Field(default=None,max_length=30000)
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class ServiceObjectiveUpdate(ServiceObjectiveCreate):
    revision:int=Field(ge=1)
class ServiceObjectiveRead(ServiceObjectiveCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class ServiceObjectivePage(StrictSchema):
    items:list[ServiceObjectiveRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class ServiceObjectiveBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
