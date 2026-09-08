from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class DiagramDocument(TenantBase):
    __tablename__='diagram_documents'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    diagram_type: Mapped[str]=mapped_column(String(80),nullable=False,default='architecture',index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='draft',index=True)
    nodes: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    edges: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    viewport: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    node_count: Mapped[int]=mapped_column(Integer,nullable=False,default=0,index=True)
    edge_count: Mapped[int]=mapped_column(Integer,nullable=False,default=0,index=True)
    notes: Mapped[str | None]=mapped_column(String(50000),nullable=True,default=None)
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_diagram_documents_title_required'),
      CheckConstraint("diagram_type IN ('architecture','workflow','data_flow','topology','process','state_machine','lineage')",name='ck_diagram_documents_diagram_type'),
      CheckConstraint("status IN ('draft','active','in_review','retired')",name='ck_diagram_documents_status'),
      CheckConstraint('node_count >= 0',name='ck_diagram_documents_node_count_minimum'),
      CheckConstraint('node_count <= 1000',name='ck_diagram_documents_node_count_maximum'),
      CheckConstraint('edge_count >= 0',name='ck_diagram_documents_edge_count_minimum'),
      CheckConstraint('edge_count <= 3000',name='ck_diagram_documents_edge_count_maximum'),
      CheckConstraint('revision >= 1',name='ck_diagram_documents_revision'),
    )
