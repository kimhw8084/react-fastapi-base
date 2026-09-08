from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class ObservabilityEvent(TenantBase):
    __tablename__='observability_events'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    event_id: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    signal: Mapped[str]=mapped_column(String(80),nullable=False,default='log',index=True)
    severity: Mapped[str]=mapped_column(String(80),nullable=False,default='info',index=True)
    timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,index=True)
    duration_ms: Mapped[float | None]=mapped_column(Float,nullable=True,default=None,index=True)
    trace_id: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    span_id: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    parent_span_id: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None)
    operation: Mapped[str | None]=mapped_column(String(200),nullable=True,default=None,index=True)
    message: Mapped[str | None]=mapped_column(String(30000),nullable=True,default=None)
    attributes: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(event_id)) BETWEEN 1 AND 160',name='ck_observability_events_event_id_required'),
      CheckConstraint("signal IN ('log','trace','metric')",name='ck_observability_events_signal'),
      CheckConstraint("severity IN ('debug','info','warning','error','critical')",name='ck_observability_events_severity'),
      CheckConstraint('duration_ms >= 0',name='ck_observability_events_duration_ms_minimum'),
      CheckConstraint('revision >= 1',name='ck_observability_events_revision'),
    )
