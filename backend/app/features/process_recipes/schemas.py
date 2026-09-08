from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class ProcessRecipeCreate(StrictSchema):
    name: str=Field(min_length=1,max_length=160)
    version_name: str=Field(min_length=1,max_length=80)
    process: str=Field(min_length=1,max_length=160)
    status: Literal['draft','qualified','released','deprecated']=Field(default='draft',max_length=80)
    parameters: dict[str,Any]=Field(default={})
    limits: dict[str,Any]=Field(default={})
    approved_by: str | None=Field(default=None,max_length=160)
    approved_at: datetime | None=Field(default=None)
    notes: str | None=Field(default=None,max_length=50000)
    @field_validator('parameters')
    @classmethod
    def validate_parameters_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('limits')
    @classmethod
    def validate_limits_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class ProcessRecipeUpdate(ProcessRecipeCreate):
    revision:int=Field(ge=1)
class ProcessRecipeRead(ProcessRecipeCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class ProcessRecipePage(StrictSchema):
    items:list[ProcessRecipeRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class ProcessRecipeBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
