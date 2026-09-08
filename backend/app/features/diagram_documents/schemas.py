from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class DiagramDocumentCreate(StrictSchema):
    title: str=Field(min_length=1,max_length=200)
    diagram_type: Literal['architecture','workflow','data_flow','topology','process','state_machine','lineage']=Field(default='architecture',max_length=80)
    status: Literal['draft','active','in_review','retired']=Field(default='draft',max_length=80)
    nodes: dict[str,Any]=Field(default={})
    edges: dict[str,Any]=Field(default={})
    viewport: dict[str,Any]=Field(default={})
    node_count: int=Field(default=0,ge=0,le=1000)
    edge_count: int=Field(default=0,ge=0,le=3000)
    notes: str | None=Field(default=None,max_length=50000)
    @field_validator('nodes')
    @classmethod
    def validate_nodes_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>300000:raise ValueError('JSON object exceeds 300000 bytes.')
        return value
    @field_validator('edges')
    @classmethod
    def validate_edges_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>300000:raise ValueError('JSON object exceeds 300000 bytes.')
        return value
    @field_validator('viewport')
    @classmethod
    def validate_viewport_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>20000:raise ValueError('JSON object exceeds 20000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class DiagramDocumentUpdate(DiagramDocumentCreate):
    revision:int=Field(ge=1)
class DiagramDocumentRead(DiagramDocumentCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class DiagramDocumentPage(StrictSchema):
    items:list[DiagramDocumentRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class DiagramDocumentBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
