from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class WaferRun(TenantBase):
    __tablename__='wafer_runs'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    wafer_id: Mapped[str]=mapped_column(String(120),nullable=False,index=True)
    lot_id: Mapped[str]=mapped_column(String(120),nullable=False,index=True)
    process_step: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='complete',index=True)
    die_rows: Mapped[int]=mapped_column(Integer,nullable=False)
    die_cols: Mapped[int]=mapped_column(Integer,nullable=False)
    bin_map: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    total_die: Mapped[int]=mapped_column(Integer,nullable=False,default=0,index=True)
    good_die: Mapped[int]=mapped_column(Integer,nullable=False,default=0,index=True)
    defect_count: Mapped[int]=mapped_column(Integer,nullable=False,default=0,index=True)
    yield_percent: Mapped[float]=mapped_column(Float,nullable=False,default=0.0,index=True)
    completed_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True,default=None,index=True)
    notes: Mapped[str | None]=mapped_column(String(50000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(wafer_id)) BETWEEN 1 AND 120',name='ck_wafer_runs_wafer_id_required'),
      CheckConstraint('length(trim(lot_id)) BETWEEN 1 AND 120',name='ck_wafer_runs_lot_id_required'),
      CheckConstraint('length(trim(process_step)) BETWEEN 1 AND 160',name='ck_wafer_runs_process_step_required'),
      CheckConstraint("status IN ('queued','processing','complete','hold','scrapped')",name='ck_wafer_runs_status'),
      CheckConstraint('die_rows >= 1',name='ck_wafer_runs_die_rows_minimum'),
      CheckConstraint('die_rows <= 100',name='ck_wafer_runs_die_rows_maximum'),
      CheckConstraint('die_cols >= 1',name='ck_wafer_runs_die_cols_minimum'),
      CheckConstraint('die_cols <= 100',name='ck_wafer_runs_die_cols_maximum'),
      CheckConstraint('yield_percent >= 0',name='ck_wafer_runs_yield_percent_minimum'),
      CheckConstraint('yield_percent <= 100',name='ck_wafer_runs_yield_percent_maximum'),
      CheckConstraint('revision >= 1',name='ck_wafer_runs_revision'),
    )
