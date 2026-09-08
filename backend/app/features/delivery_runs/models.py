from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class DeliveryRun(TenantBase):
    __tablename__='delivery_runs'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    run_id: Mapped[str]=mapped_column(String(120),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='queued',index=True)
    environment: Mapped[str]=mapped_column(String(80),nullable=False,default='staging',index=True)
    commit_sha: Mapped[str | None]=mapped_column(String(80),nullable=True,default=None,index=True)
    branch: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,index=True)
    completed_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True,default=None,index=True)
    duration_minutes: Mapped[float]=mapped_column(Float,nullable=False,default=0.0,index=True)
    stages: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    artifacts: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    triggered_by: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(run_id)) BETWEEN 1 AND 120',name='ck_delivery_runs_run_id_required'),
      CheckConstraint("status IN ('queued','running','passed','failed','cancelled')",name='ck_delivery_runs_status'),
      CheckConstraint("environment IN ('development','test','staging','production')",name='ck_delivery_runs_environment'),
      CheckConstraint('duration_minutes >= 0',name='ck_delivery_runs_duration_minutes_minimum'),
      CheckConstraint('revision >= 1',name='ck_delivery_runs_revision'),
    )
