from datetime import date,datetime
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class Rack(TenantBase):
    __tablename__='racks'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    name: Mapped[str]=mapped_column(String(120),nullable=False,index=True)
    site: Mapped[str]=mapped_column(String(120),nullable=False,index=True)
    row_name: Mapped[str | None]=mapped_column(String(80),nullable=True,default=None,index=True)
    rack_units: Mapped[int]=mapped_column(Integer,nullable=False,default=42,index=True)
    power_capacity_kw: Mapped[float]=mapped_column(Float,nullable=False,default=10.0,index=True)
    pdu_a_capacity_kw: Mapped[float|None]=mapped_column(Float,nullable=True,default=None)
    pdu_b_capacity_kw: Mapped[float|None]=mapped_column(Float,nullable=True,default=None)
    weight_capacity_kg: Mapped[float|None]=mapped_column(Float,nullable=True,default=None)
    thermal_capacity_kw: Mapped[float|None]=mapped_column(Float,nullable=True,default=None)
    reserved_units: Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    reserved_power_kw: Mapped[float]=mapped_column(Float,nullable=False,default=0.0)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='active',index=True)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(name)) BETWEEN 1 AND 120',name='ck_racks_name_required'),
      CheckConstraint('length(trim(site)) BETWEEN 1 AND 120',name='ck_racks_site_required'),
      CheckConstraint('rack_units >= 1',name='ck_racks_rack_units_minimum'),
      CheckConstraint('rack_units <= 1000',name='ck_racks_rack_units_maximum'),
      CheckConstraint('power_capacity_kw >= 0',name='ck_racks_power_capacity_kw_minimum'),
      CheckConstraint('pdu_a_capacity_kw IS NULL OR pdu_a_capacity_kw >= 0',name='ck_racks_pdu_a_capacity_minimum'),
      CheckConstraint('pdu_b_capacity_kw IS NULL OR pdu_b_capacity_kw >= 0',name='ck_racks_pdu_b_capacity_minimum'),
      CheckConstraint('weight_capacity_kg IS NULL OR weight_capacity_kg >= 0',name='ck_racks_weight_capacity_minimum'),
      CheckConstraint('thermal_capacity_kw IS NULL OR thermal_capacity_kw >= 0',name='ck_racks_thermal_capacity_minimum'),
      CheckConstraint('reserved_units >= 0 AND reserved_units <= rack_units',name='ck_racks_reserved_units_bounds'),
      CheckConstraint('reserved_power_kw >= 0 AND reserved_power_kw <= power_capacity_kw',name='ck_racks_reserved_power_bounds'),
      CheckConstraint("status IN ('active','maintenance','retired')",name='ck_racks_status'),
      CheckConstraint('revision >= 1',name='ck_racks_revision'),
    )
