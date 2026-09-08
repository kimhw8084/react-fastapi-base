from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class ProcessMeasurement(TenantBase):
    __tablename__='process_measurements'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    sample_label: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    process: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    metric: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    value: Mapped[float]=mapped_column(Float,nullable=False,index=True)
    unit: Mapped[str | None]=mapped_column(String(32),nullable=True,default=None,index=True)
    sampled_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,index=True)
    subgroup: Mapped[str | None]=mapped_column(String(80),nullable=True,default=None,index=True)
    target: Mapped[float | None]=mapped_column(Float,nullable=True,default=None)
    lower_spec: Mapped[float | None]=mapped_column(Float,nullable=True,default=None)
    upper_spec: Mapped[float | None]=mapped_column(Float,nullable=True,default=None)
    lot: Mapped[str | None]=mapped_column(String(120),nullable=True,default=None,index=True)
    category: Mapped[str]=mapped_column(String(80),nullable=False,default='measurement',index=True)
    context: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(sample_label)) BETWEEN 1 AND 160',name='ck_process_measurements_sample_label_required'),
      CheckConstraint('length(trim(process)) BETWEEN 1 AND 160',name='ck_process_measurements_process_required'),
      CheckConstraint('length(trim(metric)) BETWEEN 1 AND 160',name='ck_process_measurements_metric_required'),
      CheckConstraint("category IN ('measurement','defect','alarm','quality')",name='ck_process_measurements_category'),
      CheckConstraint('revision >= 1',name='ck_process_measurements_revision'),
    )
