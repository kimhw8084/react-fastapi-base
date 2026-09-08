from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Callable, Any
from uuid import uuid4
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import DurableJob, utcnow
from app.platform.schemas import JobRead
from app.platform.security import Actor

JobHandler=Callable[[dict[str,Any]],dict[str,Any]|None]

def enqueue(session:Session,actor:Actor,job_type:str,payload:dict[str,Any],*,max_attempts:int=3,run_after:datetime|None=None)->JobRead:
    actor.require('write')
    if not job_type or len(job_type)>80 or any(not(c.isalnum() or c in '._-') for c in job_type):raise AppError(422,'invalid_job_type','Job type is invalid.')
    if len(str(payload))>100_000:raise AppError(413,'job_payload_too_large','Job payload is too large.')
    row=DurableJob(id=str(uuid4()),job_type=job_type,status='queued',payload=payload,max_attempts=max_attempts,run_after=run_after or utcnow(),created_by=actor.user_id,updated_at=utcnow())
    session.add(row);session.flush();return JobRead.model_validate(row)

def list_jobs(session:Session,actor:Actor,*,limit:int=100,status:str|None=None)->list[JobRead]:
    actor.require('admin');query=select(DurableJob).order_by(DurableJob.created_at.desc()).limit(limit)
    if status:query=query.where(DurableJob.status==status)
    return [JobRead.model_validate(row) for row in session.scalars(query).all()]

def cancel(session:Session,actor:Actor,job_id:str)->JobRead:
    actor.require('admin');row=session.get(DurableJob,job_id)
    if not row:raise AppError(404,'job_missing','Job is not available.')
    if row.status not in ('queued','failed'):raise AppError(409,'job_not_cancellable','Only queued or failed jobs can be cancelled.')
    row.status='cancelled';row.lease_owner=None;row.lease_expires_at=None;row.updated_at=utcnow();session.flush();return JobRead.model_validate(row)

def lease_next(session:Session,worker_id:str,*,lease_seconds:int=60)->DurableJob|None:
    now=datetime.now(timezone.utc);expires=now+timedelta(seconds=lease_seconds)
    query=select(DurableJob).where(DurableJob.status.in_(('queued','running')),DurableJob.run_after<=now,or_(DurableJob.status=='queued',DurableJob.lease_expires_at.is_(None),DurableJob.lease_expires_at<now)).order_by(DurableJob.run_after,DurableJob.created_at).limit(1)
    row=session.scalars(query).first()
    if not row:return None
    row.status='running';row.lease_owner=worker_id;row.lease_expires_at=expires;row.attempts+=1;row.updated_at=utcnow();session.flush();return row

def finish(session:Session,row:DurableJob,worker_id:str,*,result:dict[str,Any]|None=None,error:str|None=None)->None:
    if row.status!='running' or row.lease_owner!=worker_id:raise AppError(409,'job_lease_lost','Job lease is not owned by this worker.')
    row.lease_owner=None;row.lease_expires_at=None;row.updated_at=utcnow()
    if error is None:row.status='succeeded';row.result=result or {};row.error=None
    elif row.attempts>=row.max_attempts:row.status='failed';row.error=error[:4000]
    else:row.status='queued';row.error=error[:4000];row.run_after=datetime.now(timezone.utc)+timedelta(seconds=min(300,2**row.attempts))
    session.flush()

def run_once(session:Session,worker_id:str,handlers:dict[str,JobHandler])->JobRead|None:
    row=lease_next(session,worker_id)
    if not row:return None
    handler=handlers.get(row.job_type)
    if handler is None:finish(session,row,worker_id,error='No registered handler for job type.');return JobRead.model_validate(row)
    try:finish(session,row,worker_id,result=handler(dict(row.payload or {})))
    except Exception as error:finish(session,row,worker_id,error=f'{type(error).__name__}: {error}')
    return JobRead.model_validate(row)

def process_one(database,tenant_id:str,worker_id:str,handlers:dict[str,JobHandler])->JobRead|None:
    """Claim transaction -> execute outside DB lock -> finish transaction.

    A crashed worker leaves a bounded lease that can be reclaimed later. External
    network calls therefore never hold SQLite's write lock.
    """
    from app.platform.transactions import write_transaction
    with write_transaction(database,tenant_id) as session:
        row=lease_next(session,worker_id)
        if row is None:return None
        job_id=row.id;job_type=row.job_type;payload=dict(row.payload or {})
    handler=handlers.get(job_type);result=None;error=None
    try:
        if handler is None:raise RuntimeError('No registered handler for job type.')
        result=handler(payload)
    except Exception as exc:error=f'{type(exc).__name__}: {exc}'
    with write_transaction(database,tenant_id) as session:
        current=session.get(DurableJob,job_id)
        if current is None:raise RuntimeError('Claimed job disappeared.')
        finish(session,current,worker_id,result=result,error=error)
        return JobRead.model_validate(current)
