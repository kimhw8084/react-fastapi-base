from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class ServiceObjective(TenantBase):
    __tablename__='service_objectives'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    name: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    window_days: Mapped[int]=mapped_column(Integer,nullable=False,default=30,index=True)
    target_percent: Mapped[float]=mapped_column(Float,nullable=False,default=99.9,index=True)
    current_percent: Mapped[float]=mapped_column(Float,nullable=False,default=100.0,index=True)
    error_budget_remaining: Mapped[float]=mapped_column(Float,nullable=False,default=100.0,index=True)
    burn_rate: Mapped[float]=mapped_column(Float,nullable=False,default=0.0,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='healthy',index=True)
    notes: Mapped[str | None]=mapped_column(String(30000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(name)) BETWEEN 1 AND 200',name='ck_service_objectives_name_required'),
      CheckConstraint('window_days >= 1',name='ck_service_objectives_window_days_minimum'),
      CheckConstraint('window_days <= 365',name='ck_service_objectives_window_days_maximum'),
      CheckConstraint('target_percent >= 0.001',name='ck_service_objectives_target_percent_minimum'),
      CheckConstraint('target_percent <= 100',name='ck_service_objectives_target_percent_maximum'),
      CheckConstraint('current_percent >= 0',name='ck_service_objectives_current_percent_minimum'),
      CheckConstraint('current_percent <= 100',name='ck_service_objectives_current_percent_maximum'),
      CheckConstraint('error_budget_remaining >= 0',name='ck_service_objectives_error_budget_remaining_minimum'),
      CheckConstraint('error_budget_remaining <= 100',name='ck_service_objectives_error_budget_remaining_maximum'),
      CheckConstraint('burn_rate >= 0',name='ck_service_objectives_burn_rate_minimum'),
      CheckConstraint("status IN ('healthy','warning','exhausted')",name='ck_service_objectives_status'),
      CheckConstraint('revision >= 1',name='ck_service_objectives_revision'),
    )
