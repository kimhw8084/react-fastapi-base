from datetime import datetime
from typing import Literal
from pydantic import Field, field_validator, model_validator
from app.platform.schemas import StrictSchema, ViewDefinition

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

class MatchingBulkRequest(StrictSchema):
    action: Literal['archive','restore']
    view: ViewDefinition
    expected_total: int = Field(ge=0, le=10000)
    fingerprint: str = Field(min_length=64, max_length=64)

class MatchingBulkPreview(StrictSchema):
    total: int = Field(ge=0, le=10000)
    fingerprint: str = Field(min_length=64, max_length=64)
    sample: list[WorkItemRead] = Field(max_length=20)

class ImportPreviewRequest(StrictSchema):
    csv: str|None = Field(default=None,max_length=500000)
    xlsx_base64: str|None = Field(default=None,max_length=700000)
    @model_validator(mode='after')
    def one_format(self):
        if (self.csv is None)==(self.xlsx_base64 is None):raise ValueError('Provide exactly one CSV or XLSX payload.')
        return self

class ImportPreview(StrictSchema):
    rows: list[WorkItemCreate]
    errors: list[str]
    fingerprint: str

class ImportCommit(StrictSchema):
    csv: str|None = Field(default=None,max_length=500000)
    xlsx_base64: str|None = Field(default=None,max_length=700000)
    fingerprint: str = Field(min_length=64, max_length=64)
    @model_validator(mode='after')
    def one_format(self):
        if (self.csv is None)==(self.xlsx_base64 is None):raise ValueError('Provide exactly one CSV or XLSX payload.')
        return self
