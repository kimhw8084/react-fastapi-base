from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class RiskCreate(StrictSchema):
    title: str=Field(min_length=1,max_length=200)
    status: Literal['identified','assessing','mitigating','monitoring','closed']=Field(default='identified',max_length=80)
    category: Literal['design','process','hardware','software','network','human','environment']=Field(default='process',max_length=80)
    severity: int=Field(default=5,ge=1,le=10)
    occurrence: int=Field(default=5,ge=1,le=10)
    detection: int=Field(default=5,ge=1,le=10)
    rpn: int=Field(default=125,ge=1,le=1000)
    residual_severity: int | None=Field(default=None,ge=1,le=10)
    residual_occurrence: int | None=Field(default=None,ge=1,le=10)
    residual_detection: int | None=Field(default=None,ge=1,le=10)
    residual_rpn: int | None=Field(default=None,ge=1,le=1000)
    effect: str | None=Field(default=None,max_length=20000)
    causes: dict[str,Any]=Field(default={})
    mitigations: dict[str,Any]=Field(default={})
    prevention: dict[str,Any]=Field(default={})
    @field_validator('causes')
    @classmethod
    def validate_causes_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('mitigations')
    @classmethod
    def validate_mitigations_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('prevention')
    @classmethod
    def validate_prevention_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class RiskUpdate(RiskCreate):
    revision:int=Field(ge=1)
class RiskRead(RiskCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class RiskPage(StrictSchema):
    items:list[RiskRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class RiskBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RiskScore(StrictSchema):
    severity:int=Field(ge=1,le=10);occurrence:int=Field(ge=1,le=10);detection:int=Field(ge=1,le=10)
    residual_severity:int|None=Field(default=None,ge=1,le=10);residual_occurrence:int|None=Field(default=None,ge=1,le=10);residual_detection:int|None=Field(default=None,ge=1,le=10)
class RiskScoreTarget(StrictSchema):
    id:str;revision:int=Field(ge=1);score:RiskScore
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
