from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class WaferRunCreate(StrictSchema):
    wafer_id: str=Field(min_length=1,max_length=120)
    lot_id: str=Field(min_length=1,max_length=120)
    process_step: str=Field(min_length=1,max_length=160)
    status: Literal['queued','processing','complete','hold','scrapped']=Field(default='complete',max_length=80)
    die_rows: int=Field(ge=1,le=100)
    die_cols: int=Field(ge=1,le=100)
    bin_map: dict[str,Any]=Field(default={})
    total_die: int=Field(default=0)
    good_die: int=Field(default=0)
    defect_count: int=Field(default=0)
    yield_percent: float=Field(default=0.0,ge=0,le=100)
    completed_at: datetime | None=Field(default=None)
    notes: str | None=Field(default=None,max_length=50000)
    @field_validator('bin_map')
    @classmethod
    def validate_bin_map_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class WaferRunUpdate(WaferRunCreate):
    revision:int=Field(ge=1)
class WaferRunRead(WaferRunCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class WaferRunPage(StrictSchema):
    items:list[WaferRunRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class WaferRunBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
