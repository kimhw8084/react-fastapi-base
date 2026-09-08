from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class PlanTask(TenantBase):
    __tablename__='plan_tasks'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='planned',index=True)
    start_date: Mapped[date]=mapped_column(Date,nullable=False,index=True)
    end_date: Mapped[date]=mapped_column(Date,nullable=False,index=True)
    baseline_start: Mapped[date | None]=mapped_column(Date,nullable=True,default=None,index=True)
    baseline_end: Mapped[date | None]=mapped_column(Date,nullable=True,default=None,index=True)
    progress: Mapped[float]=mapped_column(Float,nullable=False,default=0.0,index=True)
    milestone: Mapped[bool]=mapped_column(Boolean,nullable=False,default=False,index=True)
    owner: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    duration_days: Mapped[int]=mapped_column(Integer,nullable=False,default=1,index=True)
    notes: Mapped[str | None]=mapped_column(String(20000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_plan_tasks_title_required'),
      CheckConstraint("status IN ('planned','ready','in_progress','blocked','done','cancelled')",name='ck_plan_tasks_status'),
      CheckConstraint('progress >= 0',name='ck_plan_tasks_progress_minimum'),
      CheckConstraint('progress <= 100',name='ck_plan_tasks_progress_maximum'),
      CheckConstraint('duration_days >= 1',name='ck_plan_tasks_duration_days_minimum'),
      CheckConstraint('duration_days <= 3650',name='ck_plan_tasks_duration_days_maximum'),
      CheckConstraint('revision >= 1',name='ck_plan_tasks_revision'),
    )
