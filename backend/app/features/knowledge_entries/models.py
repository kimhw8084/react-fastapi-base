from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class KnowledgeEntrie(TenantBase):
    __tablename__='knowledge_entries'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    entry_type: Mapped[str]=mapped_column(String(80),nullable=False,default='runbook',index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='draft',index=True)
    criticality: Mapped[str]=mapped_column(String(80),nullable=False,default='standard',index=True)
    owner: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    review_state: Mapped[str]=mapped_column(String(80),nullable=False,default='needs_review',index=True)
    next_review_at: Mapped[date | None]=mapped_column(Date,nullable=True,default=None,index=True)
    content: Mapped[str | None]=mapped_column(String(100000),nullable=True,default=None)
    procedures: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    tags: Mapped[list[str]]=mapped_column(JSON,nullable=False,default=[])
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_knowledge_entries_title_required'),
      CheckConstraint("entry_type IN ('runbook','procedure','troubleshooting','architecture_note','lesson','standard','faq')",name='ck_knowledge_entries_entry_type'),
      CheckConstraint("status IN ('draft','published','archived_reference')",name='ck_knowledge_entries_status'),
      CheckConstraint("criticality IN ('standard','critical')",name='ck_knowledge_entries_criticality'),
      CheckConstraint("review_state IN ('needs_review','verified','stale','deprecated','emergency_only')",name='ck_knowledge_entries_review_state'),
      CheckConstraint('revision >= 1',name='ck_knowledge_entries_revision'),
    )
