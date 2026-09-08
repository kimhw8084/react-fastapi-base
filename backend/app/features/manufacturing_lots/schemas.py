from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class ManufacturingLotCreate(StrictSchema):
    lot_id: str=Field(min_length=1,max_length=120)
    product: str=Field(min_length=1,max_length=160)
    status: Literal['queued','running','hold','complete','scrapped']=Field(default='queued',max_length=80)
    current_step: str | None=Field(default=None,max_length=160)
    priority: Literal['low','normal','high','hot']=Field(default='normal',max_length=80)
    quantity: int=Field(default=0,ge=0)
    started_at: datetime | None=Field(default=None)
    target_complete: datetime | None=Field(default=None)
    route: dict[str,Any]=Field(default={})
    hold_reason: str | None=Field(default=None,max_length=10000)
    owner: str | None=Field(default=None,max_length=160)
    @field_validator('route')
    @classmethod
    def validate_route_size(cls,value):
        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>50000:raise ValueError('JSON object exceeds 50000 bytes.')
        return value
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class ManufacturingLotUpdate(ManufacturingLotCreate):
    revision:int=Field(ge=1)
class ManufacturingLotRead(ManufacturingLotCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class ManufacturingLotPage(StrictSchema):
    items:list[ManufacturingLotRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class ManufacturingLotBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
