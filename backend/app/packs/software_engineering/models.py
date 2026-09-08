from __future__ import annotations
from datetime import datetime,timezone
from math import isfinite
from typing import Any

def _duration_minutes(start:datetime,end:datetime|None)->float:
    if end is None:end=datetime.now(timezone.utc)
    if start.tzinfo is None:start=start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:end=end.replace(tzinfo=timezone.utc)
    if end<start:raise ValueError('End time must not precede start time.')
    return (end-start).total_seconds()/60.0

def normalize_delivery(values:dict[str,Any])->dict[str,Any]:
    values=dict(values);values['duration_minutes']=_duration_minutes(values['started_at'],values.get('completed_at'))
    stages=values.get('stages') or {}
    if not isinstance(stages,dict):raise ValueError('Delivery stages must be an object.')
    items=stages.get('items',[])
    if not isinstance(items,list) or len(items)>200:raise ValueError('Delivery run supports at most 200 stages.')
    normalized=[];ids=set();allowed={'id','name','status','started_at','completed_at','duration_seconds','message'}
    for index,item in enumerate(items):
        if not isinstance(item,dict) or set(item)-allowed:raise ValueError('Delivery stage contains unsupported fields.')
        sid=str(item.get('id',index+1)).strip();name=str(item.get('name','')).strip();status=str(item.get('status','queued')).strip()
        if not sid or len(sid)>64 or sid in ids:raise ValueError('Delivery stage ids must be distinct and at most 64 characters.')
        if not name or len(name)>160:raise ValueError('Delivery stage name is required and limited to 160 characters.')
        if status not in {'queued','running','passed','failed','skipped','cancelled'}:raise ValueError('Delivery stage status is invalid.')
        ids.add(sid);normalized.append({**item,'id':sid,'name':name,'status':status})
    values['stages']={'items':normalized};return values

def normalize_incident(values:dict[str,Any])->dict[str,Any]:
    values=dict(values);values['duration_minutes']=_duration_minutes(values['started_at'],values.get('resolved_at'))
    timeline=values.get('timeline') or {}
    if not isinstance(timeline,dict):raise ValueError('Incident timeline must be an object.')
    events=timeline.get('events',[])
    if not isinstance(events,list) or len(events)>1000:raise ValueError('Incident timeline supports at most 1,000 events.')
    normalized=[]
    for event in events:
        if not isinstance(event,dict) or set(event)-{'at','kind','message','actor'}:raise ValueError('Incident timeline event contains unsupported fields.')
        message=str(event.get('message','')).strip();kind=str(event.get('kind','update')).strip()
        if not message or len(message)>5000:raise ValueError('Incident timeline message is required and limited to 5,000 characters.')
        if kind not in {'detected','update','mitigation','decision','recovery','resolved'}:raise ValueError('Incident timeline event kind is invalid.')
        normalized.append({**event,'kind':kind,'message':message})
    values['timeline']={'events':normalized};return values

def normalize_slo(values:dict[str,Any])->dict[str,Any]:
    values=dict(values);target=float(values['target_percent']);current=float(values['current_percent'])
    if not isfinite(target) or not isfinite(current) or not 0<target<100 or not 0<=current<=100:raise ValueError('SLO percentages must be finite and target must be between 0 and 100.')
    allowed_error=100.0-target;actual_error=100.0-current;burn=max(0.0,actual_error/allowed_error);remaining=max(0.0,min(100.0,(1.0-burn)*100.0))
    values['burn_rate']=burn;values['error_budget_remaining']=remaining;values['status']='exhausted' if remaining<=0 else 'warning' if remaining<25 or burn>=.75 else 'healthy';return values

def normalize_observability(values:dict[str,Any])->dict[str,Any]:
    values=dict(values);duration=values.get('duration_ms')
    if duration is not None and (not isfinite(float(duration)) or float(duration)<0):raise ValueError('Observability duration must be a finite non-negative number.')
    for key in ('trace_id','span_id','parent_span_id'):
        value=values.get(key)
        if value is not None and len(str(value))>160:raise ValueError(f'{key} is too long.')
    return values
