from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class Research(TenantBase):
    __tablename__='research'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='question',index=True)
    phase: Mapped[str]=mapped_column(String(80),nullable=False,default='discovery',index=True)
    question: Mapped[str]=mapped_column(String(20000),nullable=False)
    hypothesis: Mapped[str | None]=mapped_column(String(60000),nullable=True,default=None)
    methodology: Mapped[str | None]=mapped_column(String(60000),nullable=True,default=None)
    experiments: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    evidence: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    analysis: Mapped[str | None]=mapped_column(String(80000),nullable=True,default=None)
    findings: Mapped[str | None]=mapped_column(String(80000),nullable=True,default=None)
    conclusion: Mapped[str | None]=mapped_column(String(60000),nullable=True,default=None)
    recommendation: Mapped[str | None]=mapped_column(String(60000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_research_title_required'),
      CheckConstraint("status IN ('question','researching','experimenting','analyzing','review','complete')",name='ck_research_status'),
      CheckConstraint("phase IN ('discovery','hypothesis','experiment','analysis','conclusion')",name='ck_research_phase'),
      CheckConstraint('length(trim(question)) BETWEEN 1 AND 20000',name='ck_research_question_required'),
      CheckConstraint('revision >= 1',name='ck_research_revision'),
    )
