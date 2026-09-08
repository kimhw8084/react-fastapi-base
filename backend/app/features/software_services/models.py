from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class SoftwareService(TenantBase):
    __tablename__='software_services'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    name: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='healthy',index=True)
    tier: Mapped[str]=mapped_column(String(80),nullable=False,default='tier_2',index=True)
    owner: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    repository: Mapped[str | None]=mapped_column(String(500),nullable=True,default=None,index=True)
    runtime: Mapped[str | None]=mapped_column(String(120),nullable=True,default=None,index=True)
    environment: Mapped[str]=mapped_column(String(80),nullable=False,default='production',index=True)
    config: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    description: Mapped[str | None]=mapped_column(String(50000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(name)) BETWEEN 1 AND 160',name='ck_software_services_name_required'),
      CheckConstraint("status IN ('healthy','degraded','maintenance','retired')",name='ck_software_services_status'),
      CheckConstraint("tier IN ('tier_0','tier_1','tier_2','tier_3')",name='ck_software_services_tier'),
      CheckConstraint("environment IN ('development','test','staging','production')",name='ck_software_services_environment'),
      CheckConstraint('revision >= 1',name='ck_software_services_revision'),
    )
