from datetime import datetime
from typing import Literal
from pydantic import Field, field_validator
from app.platform.schemas import StrictSchema

class ProjectCreate(StrictSchema):
    title: str=Field(min_length=1,max_length=160)
    summary: str=Field(default='',max_length=10000)
    status: Literal['planned','active','blocked','complete']='planned'
    owner: str=Field(default='',max_length=120)
    @field_validator('title','owner')
    @classmethod
    def trim_text(cls,value):return value.strip()

class ProjectUpdate(ProjectCreate):
    revision: int=Field(ge=1)
class ProjectRead(ProjectCreate):
    id: str;revision: int;archived: bool;created_by: str;created_at: datetime;updated_at: datetime
class ProjectPage(StrictSchema):
    items:list[ProjectRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class ProjectBulkRequest(StrictSchema):
    action: Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
