from datetime import date,datetime
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class Equipment(TenantBase):
    __tablename__='equipment'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    name: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    kind: Mapped[str]=mapped_column(String(80),nullable=False,default='server',index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='active',index=True)
    serial: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    power_kw: Mapped[float]=mapped_column(Float,nullable=False,default=0.0,index=True)
    notes: Mapped[str | None]=mapped_column(String(10000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(name)) BETWEEN 1 AND 160',name='ck_equipment_name_required'),
      CheckConstraint("kind IN ('server','switch','storage','appliance','other')",name='ck_equipment_kind'),
      CheckConstraint("status IN ('active','maintenance','offline','retired')",name='ck_equipment_status'),
      CheckConstraint('power_kw >= 0',name='ck_equipment_power_kw_minimum'),
      CheckConstraint('revision >= 1',name='ck_equipment_revision'),
    )
