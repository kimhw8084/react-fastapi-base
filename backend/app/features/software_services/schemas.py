from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class SoftwareServiceCreate(StrictSchema):
    name: str=Field(min_length=1,max_length=160)
    status: Literal['healthy','degraded','maintenance','retired']=Field(default='healthy',max_length=80)
    tier: Literal['tier_0','tier_1','tier_2','tier_3']=Field(default='tier_2',max_length=80)
    owner: str | None=Field(default=None,max_length=160)
    repository: str | None=Field(default=None,max_length=500)
    runtime: str | None=Field(default=None,max_length=120)
    environment: Literal['development','test','staging','production']=Field(default='production',max_length=80)
    config: dict[str,Any]=Field(default={})
    description: str | None=Field(default=None,max_length=50000)
    @field_validator('config')
    @classmethod
    def validate_config_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class SoftwareServiceUpdate(SoftwareServiceCreate):
    revision:int=Field(ge=1)
class SoftwareServiceRead(SoftwareServiceCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class SoftwareServicePage(StrictSchema):
    items:list[SoftwareServiceRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class SoftwareServiceBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
