from datetime import date,datetime
from typing import Literal
from pydantic import Field,field_validator,model_validator
from app.platform.schemas import StrictSchema

class RackCreate(StrictSchema):
    name: str=Field(min_length=1,max_length=120)
    site: str=Field(min_length=1,max_length=120)
    row_name: str | None=Field(default=None,max_length=80)
    rack_units: int=Field(default=42,ge=1,le=1000)
    power_capacity_kw: float=Field(default=10.0,ge=0)
    pdu_a_capacity_kw: float|None=Field(default=None,ge=0)
    pdu_b_capacity_kw: float|None=Field(default=None,ge=0)
    weight_capacity_kg: float|None=Field(default=None,ge=0)
    thermal_capacity_kw: float|None=Field(default=None,ge=0)
    reserved_units: int=Field(default=0,ge=0)
    reserved_power_kw: float=Field(default=0.0,ge=0)
    status: Literal['active','maintenance','retired']=Field(default='active',max_length=80)
    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
    @model_validator(mode='after')
    def validate_capacity_reservations(self):
        if self.reserved_units>self.rack_units:raise ValueError('Reserved rack units cannot exceed rack capacity.')
        if self.reserved_power_kw>self.power_capacity_kw:raise ValueError('Reserved power cannot exceed rack capacity.')
        return self
class RackUpdate(RackCreate):
    revision:int=Field(ge=1)
class RackRead(RackCreate):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class RackPage(StrictSchema):
    items:list[RackRead];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class RackBulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
