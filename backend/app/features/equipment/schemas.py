from datetime import date,datetime
from typing import Literal
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class EquipmentCreate(StrictSchema):
    name: str=Field(min_length=1,max_length=160)
    kind: Literal['server','switch','storage','appliance','other']=Field(default='server',max_length=80)
    status: Literal['active','maintenance','offline','retired']=Field(default='active',max_length=80)
    serial: str | None=Field(default=None,max_length=160)
    power_kw: float=Field(default=0.0,ge=0)
    notes: str | None=Field(default=None,max_length=10000)
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class EquipmentUpdate(EquipmentCreate):
    revision:int=Field(ge=1)
class EquipmentRead(EquipmentCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class EquipmentPage(StrictSchema):
    items:list[EquipmentRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class EquipmentBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
