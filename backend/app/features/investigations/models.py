from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class Investigation(TenantBase):
    __tablename__='investigations'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='open',index=True)
    priority: Mapped[str]=mapped_column(String(80),nullable=False,default='medium',index=True)
    problem: Mapped[str]=mapped_column(String(20000),nullable=False)
    evidence: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    hypotheses: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    causes: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    actions: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    findings: Mapped[str | None]=mapped_column(String(60000),nullable=True,default=None)
    conclusion: Mapped[str | None]=mapped_column(String(60000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_investigations_title_required'),
      CheckConstraint("status IN ('open','investigating','validated','resolved','closed')",name='ck_investigations_status'),
      CheckConstraint("priority IN ('low','medium','high','critical')",name='ck_investigations_priority'),
      CheckConstraint('length(trim(problem)) BETWEEN 1 AND 20000',name='ck_investigations_problem_required'),
      CheckConstraint('revision >= 1',name='ck_investigations_revision'),
    )
