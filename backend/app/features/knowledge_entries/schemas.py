from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class KnowledgeEntrieCreate(StrictSchema):
    title: str=Field(min_length=1,max_length=200)
    entry_type: Literal['runbook','procedure','troubleshooting','architecture_note','lesson','standard','faq']=Field(default='runbook',max_length=80)
    status: Literal['draft','published','archived_reference']=Field(default='draft',max_length=80)
    criticality: Literal['standard','critical']=Field(default='standard',max_length=80)
    owner: str | None=Field(default=None,max_length=160)
    review_state: Literal['needs_review','verified','stale','deprecated','emergency_only']=Field(default='needs_review',max_length=80)
    next_review_at: date | None=Field(default=None)
    content: str | None=Field(default=None,max_length=100000)
    procedures: dict[str,Any]=Field(default={})
    tags: list[Literal['operations','recovery','maintenance','architecture','safety','quality','software','hardware','network']]=Field(default=[],max_length=100)
    @field_validator('procedures')
    @classmethod
    def validate_procedures_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class KnowledgeEntrieUpdate(KnowledgeEntrieCreate):
    revision:int=Field(ge=1)
class KnowledgeEntrieRead(KnowledgeEntrieCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class KnowledgeEntriePage(StrictSchema):
    items:list[KnowledgeEntrieRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class KnowledgeEntrieBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
