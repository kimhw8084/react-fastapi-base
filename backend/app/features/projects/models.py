from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.platform.models import TenantBase, utcnow

class Project(TenantBase):
    __tablename__='projects'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    title: Mapped[str]=mapped_column(String(160),index=True)
    summary: Mapped[str]=mapped_column(Text,default='')
    status: Mapped[str]=mapped_column(String(20),default='planned',index=True)
    owner: Mapped[str]=mapped_column(String(120),default='',index=True)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint("status IN ('planned','active','blocked','complete')",name='ck_project_status'),
      CheckConstraint('revision >= 1',name='ck_project_revision'),
      CheckConstraint('length(trim(title)) BETWEEN 1 AND 160',name='ck_project_title'),
    )
