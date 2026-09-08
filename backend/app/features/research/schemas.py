from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class ResearchCreate(StrictSchema):
    title: str=Field(min_length=1,max_length=200)
    status: Literal['question','researching','experimenting','analyzing','review','complete']=Field(default='question',max_length=80)
    phase: Literal['discovery','hypothesis','experiment','analysis','conclusion']=Field(default='discovery',max_length=80)
    question: str=Field(min_length=1,max_length=20000)
    hypothesis: str | None=Field(default=None,max_length=60000)
    methodology: str | None=Field(default=None,max_length=60000)
    experiments: dict[str,Any]=Field(default={})
    evidence: dict[str,Any]=Field(default={})
    analysis: str | None=Field(default=None,max_length=80000)
    findings: str | None=Field(default=None,max_length=80000)
    conclusion: str | None=Field(default=None,max_length=60000)
    recommendation: str | None=Field(default=None,max_length=60000)
    @field_validator('experiments')
    @classmethod
    def validate_experiments_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('evidence')
    @classmethod
    def validate_evidence_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class ResearchUpdate(ResearchCreate):
    revision:int=Field(ge=1)
class ResearchRead(ResearchCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class ResearchPage(StrictSchema):
    items:list[ResearchRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class ResearchBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
