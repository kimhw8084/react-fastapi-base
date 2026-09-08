from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class Incident(TenantBase):
    __tablename__='incidents'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    incident_number: Mapped[str]=mapped_column(String(80),nullable=False,index=True)
    title: Mapped[str]=mapped_column(String(240),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='investigating',index=True)
    severity: Mapped[str]=mapped_column(String(80),nullable=False,default='sev_3',index=True)
    started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,index=True)
    resolved_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True,default=None,index=True)
    duration_minutes: Mapped[float]=mapped_column(Float,nullable=False,default=0.0,index=True)
    commander: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    impact: Mapped[str | None]=mapped_column(String(50000),nullable=True,default=None)
    timeline: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    actions: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(incident_number)) BETWEEN 1 AND 80',name='ck_incidents_incident_number_required'),
      CheckConstraint('length(trim(title)) BETWEEN 1 AND 240',name='ck_incidents_title_required'),
      CheckConstraint("status IN ('investigating','identified','monitoring','resolved','closed')",name='ck_incidents_status'),
      CheckConstraint("severity IN ('sev_1','sev_2','sev_3','sev_4')",name='ck_incidents_severity'),
      CheckConstraint('duration_minutes >= 0',name='ck_incidents_duration_minutes_minimum'),
      CheckConstraint('revision >= 1',name='ck_incidents_revision'),
    )
