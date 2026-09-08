from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class ProcessMeasurementCreate(StrictSchema):
    sample_label: str=Field(min_length=1,max_length=160)
    process: str=Field(min_length=1,max_length=160)
    metric: str=Field(min_length=1,max_length=160)
    value: float=Field()
    unit: str | None=Field(default=None,max_length=32)
    sampled_at: datetime=Field()
    subgroup: str | None=Field(default=None,max_length=80)
    target: float | None=Field(default=None)
    lower_spec: float | None=Field(default=None)
    upper_spec: float | None=Field(default=None)
    lot: str | None=Field(default=None,max_length=120)
    category: Literal['measurement','defect','alarm','quality']=Field(default='measurement',max_length=80)
    context: dict[str,Any]=Field(default={})
    @field_validator('context')
    @classmethod
    def validate_context_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class ProcessMeasurementUpdate(ProcessMeasurementCreate):
    revision:int=Field(ge=1)
class ProcessMeasurementRead(ProcessMeasurementCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class ProcessMeasurementPage(StrictSchema):
    items:list[ProcessMeasurementRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class ProcessMeasurementBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
