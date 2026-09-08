from datetime import date,datetime
from typing import Any
from sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String
from sqlalchemy.orm import Mapped,mapped_column
from app.platform.models import TenantBase,utcnow

class Risk(TenantBase):
    __tablename__='risks'
    id: Mapped[str]=mapped_column(String(36),primary_key=True)
    title: Mapped[str]=mapped_column(String(200),nullable=False,index=True)
    status: Mapped[str]=mapped_column(String(80),nullable=False,default='identified',index=True)
    category: Mapped[str]=mapped_column(String(80),nullable=False,default='process',index=True)
    severity: Mapped[int]=mapped_column(Integer,nullable=False,default=5,index=True)
    occurrence: Mapped[int]=mapped_column(Integer,nullable=False,default=5,index=True)
    detection: Mapped[int]=mapped_column(Integer,nullable=False,default=5,index=True)
    rpn: Mapped[int]=mapped_column(Integer,nullable=False,default=125,index=True)
    residual_severity: Mapped[int | None]=mapped_column(Integer,nullable=True,default=None,index=True)
    residual_occurrence: Mapped[int | None]=mapped_column(Integer,nullable=True,default=None,index=True)
    residual_detection: Mapped[int | None]=mapped_column(Integer,nullable=True,default=None,index=True)
    residual_rpn: Mapped[int | None]=mapped_column(Integer,nullable=True,default=None,index=True)
    effect: Mapped[str | None]=mapped_column(String(20000),nullable=True,default=None)
    causes: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    mitigations: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    prevention: Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False,default={})
    revision: Mapped[int]=mapped_column(Integer,default=1)
    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)
    created_by: Mapped[str]=mapped_column(String(200))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    __table_args__=(
      CheckConstraint('length(trim(title)) BETWEEN 1 AND 200',name='ck_risks_title_required'),
      CheckConstraint("status IN ('identified','assessing','mitigating','monitoring','closed')",name='ck_risks_status'),
      CheckConstraint("category IN ('design','process','hardware','software','network','human','environment')",name='ck_risks_category'),
      CheckConstraint('severity >= 1',name='ck_risks_severity_minimum'),
      CheckConstraint('severity <= 10',name='ck_risks_severity_maximum'),
      CheckConstraint('occurrence >= 1',name='ck_risks_occurrence_minimum'),
      CheckConstraint('occurrence <= 10',name='ck_risks_occurrence_maximum'),
      CheckConstraint('detection >= 1',name='ck_risks_detection_minimum'),
      CheckConstraint('detection <= 10',name='ck_risks_detection_maximum'),
      CheckConstraint('rpn >= 1',name='ck_risks_rpn_minimum'),
      CheckConstraint('rpn <= 1000',name='ck_risks_rpn_maximum'),
      CheckConstraint('residual_severity >= 1',name='ck_risks_residual_severity_minimum'),
      CheckConstraint('residual_severity <= 10',name='ck_risks_residual_severity_maximum'),
      CheckConstraint('residual_occurrence >= 1',name='ck_risks_residual_occurrence_minimum'),
      CheckConstraint('residual_occurrence <= 10',name='ck_risks_residual_occurrence_maximum'),
      CheckConstraint('residual_detection >= 1',name='ck_risks_residual_detection_minimum'),
      CheckConstraint('residual_detection <= 10',name='ck_risks_residual_detection_maximum'),
      CheckConstraint('residual_rpn >= 1',name='ck_risks_residual_rpn_minimum'),
      CheckConstraint('residual_rpn <= 1000',name='ck_risks_residual_rpn_maximum'),
      CheckConstraint('revision >= 1',name='ck_risks_revision'),
    )
