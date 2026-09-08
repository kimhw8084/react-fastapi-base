from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class ManufacturingLot(TenantBase):
    __tablename__='manufacturing_lots'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    lot_id: Mapped[str]=mapped_column(String(120),nullable=False,index=True)
    product: Mapped[str]=mapped_column(String(160),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='queued',index=True)
    current_step: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    priority: Mapped[str]=mapped_column(String(80),nullable=False,default='normal',index=True)
    quantity: Mapped[int]=mapped_column(Integer,nullable=False,default=0,index=True)
    started_at: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True,default=None,index=True)
    target_complete: Mapped[datetime | None]=mapped_column(DateTime(timezone=True),nullable=True,default=None,index=True)
    route: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    hold_reason: Mapped[str | None]=mapped_column(String(10000),nullable=True,default=None)
    owner: Mapped[str | None]=mapped_column(String(160),nullable=True,default=None,index=True)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(lot_id)) BETWEEN 1 AND 120',name='ck_manufacturing_lots_lot_id_required'),
      CheckConstraint('length(trim(product)) BETWEEN 1 AND 160',name='ck_manufacturing_lots_product_required'),
      CheckConstraint("status IN ('queued','running','hold','complete','scrapped')",name='ck_manufacturing_lots_status'),
      CheckConstraint("priority IN ('low','normal','high','hot')",name='ck_manufacturing_lots_priority'),
      CheckConstraint('quantity >= 0',name='ck_manufacturing_lots_quantity_minimum'),
      CheckConstraint('revision >= 1',name='ck_manufacturing_lots_revision'),
    )
