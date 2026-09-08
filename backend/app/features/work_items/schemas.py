from datetime import datetime
from typing import Literal
from pydantic import Field, field_validator
from app.platform.schemas import StrictSchema

class WorkItemCreate(StrictSchema):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default='', max_length=10000)
    status: Literal['open','in_progress','done'] = 'open'
    priority: Literal['low','normal','high'] = 'normal'
    @field_validator('title')
    @classmethod
    def trim_title(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Title is required.')
        return value

class WorkItemUpdate(WorkItemCreate):
    revision: int = Field(ge=1)

class WorkItemRead(WorkItemCreate):
    id: str
    revision: int
    archived: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

class WorkItemPage(StrictSchema):
    items: list[WorkItemRead]
    total: int
    limit: int
    offset: int

class BulkTarget(StrictSchema):
    id: str
    revision: int = Field(ge=1)

class BulkRequest(StrictSchema):
    action: Literal['archive','restore']
    targets: list[BulkTarget] = Field(min_length=1, max_length=100)

class ImportPreviewRequest(StrictSchema):
    csv: str = Field(max_length=500000)

class ImportPreview(StrictSchema):
    rows: list[WorkItemCreate]
    errors: list[str]
    fingerprint: str

class ImportCommit(StrictSchema):
    csv: str = Field(max_length=500000)
    fingerprint: str = Field(min_length=64, max_length=64)
