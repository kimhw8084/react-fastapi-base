from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.platform.models import TenantBase, utcnow

class WorkItem(TenantBase):
    __tablename__ = 'work_items'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='open', index=True)
    priority: Mapped[str] = mapped_column(String(20), default='normal', index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_by: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("status IN ('open','in_progress','done')", name='ck_work_item_status'),
        CheckConstraint("priority IN ('low','normal','high')", name='ck_work_item_priority'),
        CheckConstraint('revision >= 1', name='ck_work_item_revision'),
        CheckConstraint('length(trim(title)) BETWEEN 1 AND 160', name='ck_work_item_title'),
    )
