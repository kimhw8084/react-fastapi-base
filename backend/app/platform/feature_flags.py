from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import FeatureFlag, utcnow
from app.platform.schemas import FeatureFlagRead, FeatureFlagWrite
from app.platform.security import Actor

def list_flags(session:Session,actor:Actor)->list[FeatureFlagRead]:
    actor.require('read');return [FeatureFlagRead.model_validate(row) for row in session.scalars(select(FeatureFlag).order_by(FeatureFlag.key)).all()]

def set_flag(session:Session,actor:Actor,key:str,data:FeatureFlagWrite)->FeatureFlagRead:
    actor.require('admin')
    if not key or len(key)>80 or not key[0].isalpha() or any(not(c.isalnum() or c in '._-') for c in key):raise AppError(422,'invalid_feature_flag','Feature flag key is invalid.')
    row=session.get(FeatureFlag,key)
    if row is None:
        if data.revision is not None:raise AppError(409,'revision_conflict','Feature flag does not exist yet.')
        row=FeatureFlag(key=key,enabled=data.enabled,description=data.description,rules=data.rules,revision=1,updated_by=actor.user_id,updated_at=utcnow());session.add(row)
    else:
        if data.revision!=row.revision:raise AppError(409,'revision_conflict','Feature flag changed. Refresh and retry.',{'current_revision':row.revision})
        row.enabled=data.enabled;row.description=data.description;row.rules=data.rules;row.revision+=1;row.updated_by=actor.user_id;row.updated_at=utcnow()
    session.flush();return FeatureFlagRead.model_validate(row)
