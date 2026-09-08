from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class EquipmentState(TenantBase):
    __tablename__='equipment_states'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    label: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    state: Mapped[str]=mapped_column(String(80),nullable=False,index=True)
    module: Mapped[str | None]=mapped_column(String(120),nullable=True,default=None,index=True)
    started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,index=True)
    ended_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True,default=None,index=True)
    duration_minutes: Mapped[float]=mapped_column(Float,nullable=False,default=0.0,index=True)
    reason: Mapped[str | None]=mapped_column(String(10000),nullable=True,default=None)
    alarm_code: Mapped[str | None]=mapped_column(String(80),nullable=True,default=None,index=True)
    context: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(label)) BETWEEN 1 AND 160',name='ck_equipment_states_label_required'),
      CheckConstraint("state IN ('production','standby','engineering','scheduled_down','unscheduled_down')",name='ck_equipment_states_state'),
      CheckConstraint('length(trim(state)) BETWEEN 1 AND 80',name='ck_equipment_states_state_required'),
      CheckConstraint('duration_minutes >= 0',name='ck_equipment_states_duration_minutes_minimum'),
      CheckConstraint('revision >= 1',name='ck_equipment_states_revision'),
    )
