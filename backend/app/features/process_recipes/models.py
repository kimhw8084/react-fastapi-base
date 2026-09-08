from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class ProcessRecipe(TenantBase):
    __tablename__='process_recipes'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    name: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    version_name: Mapped[str]=mapped_column(String(80),nullable=False,index=True)
    process: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='draft',index=True)
    parameters: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    limits: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    approved_by: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    approved_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True,default=None,index=True)
    notes: Mapped[str | None]=mapped_column(String(50000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(name)) BETWEEN 1 AND 160',name='ck_process_recipes_name_required'),
      CheckConstraint('length(trim(version_name)) BETWEEN 1 AND 80',name='ck_process_recipes_version_name_required'),
      CheckConstraint('length(trim(process)) BETWEEN 1 AND 160',name='ck_process_recipes_process_required'),
      CheckConstraint("status IN ('draft','qualified','released','deprecated')",name='ck_process_recipes_status'),
      CheckConstraint('revision >= 1',name='ck_process_recipes_revision'),
    )
