from __future__ import annotations
from datetime import datetime, timezone
from math import isfinite
from typing import Any

MAX_WAFER_CELLS=10_000

def normalize_wafer(values:dict[str,Any])->dict[str,Any]:
    values=dict(values)
    rows=int(values['die_rows']);cols=int(values['die_cols'])
    if not 1<=rows<=100 or not 1<=cols<=100 or rows*cols>MAX_WAFER_CELLS:
        raise ValueError('Wafer grid must contain at most 10,000 die coordinates.')
    raw=values.get('bin_map') or {}
    if not isinstance(raw,dict):raise ValueError('Bin map must be an object.')
    cells=raw.get('cells',[]);good_bins=raw.get('good_bins',['GOOD','PASS','1'])
    if not isinstance(cells,list) or len(cells)>rows*cols:raise ValueError('Bin map cells exceed wafer grid capacity.')
    if not isinstance(good_bins,list) or len(good_bins)>50 or any(not isinstance(v,str) or not v.strip() or len(v)>40 for v in good_bins):raise ValueError('good_bins must be a short list of bin labels.')
    good={v.strip().upper() for v in good_bins};seen=set();normalized=[]
    for cell in cells:
        if not isinstance(cell,dict) or set(cell)-{'x','y','bin','value','defect'}:raise ValueError('Wafer cells may only contain x, y, bin, value and defect.')
        try:x=int(cell['x']);y=int(cell['y'])
        except (KeyError,TypeError,ValueError):raise ValueError('Wafer cell coordinates must be integers.') from None
        if not 0<=x<cols or not 0<=y<rows:raise ValueError('Wafer cell coordinate is outside the declared grid.')
        if (x,y) in seen:raise ValueError('Wafer cell coordinates must be unique.')
        seen.add((x,y));bin_label=str(cell.get('bin','')).strip()
        if not bin_label or len(bin_label)>40:raise ValueError('Wafer cell bin must be 1-40 characters.')
        value=cell.get('value')
        if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(float(value))):raise ValueError('Wafer cell value must be finite when supplied.')
        defect=cell.get('defect')
        if defect is not None and (not isinstance(defect,str) or len(defect)>80):raise ValueError('Wafer defect label is too long.')
        normalized.append({'x':x,'y':y,'bin':bin_label,**({'value':float(value)} if value is not None else {}),**({'defect':defect.strip()} if isinstance(defect,str) and defect.strip() else {})})
    total=len(normalized);good_count=sum(1 for cell in normalized if str(cell['bin']).upper() in good);defects=total-good_count
    values['bin_map']={'cells':normalized,'good_bins':[value.strip() for value in good_bins]}
    values['total_die']=total;values['good_die']=good_count;values['defect_count']=defects;values['yield_percent']=(good_count/total*100.0) if total else 0.0
    return values

def normalize_lot(values:dict[str,Any])->dict[str,Any]:
    values=dict(values);route=values.get('route') or {}
    if not isinstance(route,dict):raise ValueError('Lot route must be an object.')
    steps=route.get('steps',[])
    if not isinstance(steps,list) or len(steps)>500:raise ValueError('Lot route supports at most 500 steps.')
    normalized=[];ids=set()
    for index,step in enumerate(steps):
        if not isinstance(step,dict) or set(step)-{'id','name','status','started_at','ended_at','equipment'}:raise ValueError('Lot route step contains unsupported fields.')
        sid=str(step.get('id',index+1)).strip();name=str(step.get('name','')).strip()
        if not sid or len(sid)>64 or sid in ids:raise ValueError('Lot route step ids must be distinct and at most 64 characters.')
        if not name or len(name)>160:raise ValueError('Lot route step name is required and limited to 160 characters.')
        ids.add(sid);normalized.append({**step,'id':sid,'name':name})
    values['route']={'steps':normalized}
    start=values.get('started_at');target=values.get('target_complete')
    if start and target and target<start:raise ValueError('Lot target completion must not precede its start.')
    return values

def normalize_equipment_state(values:dict[str,Any])->dict[str,Any]:
    values=dict(values);start=values['started_at'];end=values.get('ended_at')
    if end is not None and end<start:raise ValueError('Equipment state end must not precede its start.')
    reference=end or datetime.now(timezone.utc)
    if start.tzinfo is None:start=start.replace(tzinfo=timezone.utc)
    if reference.tzinfo is None:reference=reference.replace(tzinfo=timezone.utc)
    values['duration_minutes']=max(0.0,(reference-start).total_seconds()/60.0)
    return values

def recipe_diff(left:dict[str,Any],right:dict[str,Any])->list[dict[str,Any]]:
    keys=sorted(set(left)|set(right));result=[]
    for key in keys:
        before=left.get(key);after=right.get(key)
        if before!=after:result.append({'key':key,'before':before,'after':after})
    return result
