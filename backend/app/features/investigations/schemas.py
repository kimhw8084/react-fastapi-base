from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class InvestigationCreate(StrictSchema):
    title: str=Field(min_length=1,max_length=200)
    status: Literal['open','investigating','validated','resolved','closed']=Field(default='open',max_length=80)
    priority: Literal['low','medium','high','critical']=Field(default='medium',max_length=80)
    problem: str=Field(min_length=1,max_length=20000)
    evidence: dict[str,Any]=Field(default={})
    hypotheses: dict[str,Any]=Field(default={})
    causes: dict[str,Any]=Field(default={})
    actions: dict[str,Any]=Field(default={})
    findings: str | None=Field(default=None,max_length=60000)
    conclusion: str | None=Field(default=None,max_length=60000)
    @field_validator('evidence')
    @classmethod
    def validate_evidence_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('hypotheses')
    @classmethod
    def validate_hypotheses_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('causes')
    @classmethod
    def validate_causes_size(cls,value):
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
class InvestigationUpdate(InvestigationCreate):
    revision:int=Field(ge=1)
class InvestigationRead(InvestigationCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class InvestigationPage(StrictSchema):
    items:list[InvestigationRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class InvestigationBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
