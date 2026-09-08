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

def wafer_defect_summary(cells:list[dict[str,Any]],*,rows:int,cols:int,good_bins:tuple[str,...]=('GOOD','PASS','1'),edge_exclusion:int=0)->dict[str,Any]:
    if rows<1 or cols<1 or edge_exclusion<0 or edge_exclusion*2>=min(rows,cols):
        raise ValueError('Wafer dimensions and edge exclusion are invalid.')
    good={value.upper() for value in good_bins};bins:dict[str,int]={};zones={'edge':0,'center':0};defects_by_zone={'edge':0,'center':0};defects_by_bin:dict[str,int]={}
    for cell in cells:
        x=int(cell['x']);y=int(cell['y']);label=str(cell.get('bin','')).strip();
        if not 0<=x<cols or not 0<=y<rows or not label:raise ValueError('Wafer defect cells must be inside the declared grid.')
        zone='edge' if x<edge_exclusion or y<edge_exclusion or x>=cols-edge_exclusion or y>=rows-edge_exclusion else 'center';upper=label.upper();bins[upper]=bins.get(upper,0)+1;zones[zone]+=1
        if upper not in good:defects_by_zone[zone]+=1;defects_by_bin[upper]=defects_by_bin.get(upper,0)+1
    total=sum(bins.values());good_count=sum(count for label,count in bins.items() if label in good)
    return {'total_die':total,'good_die':good_count,'defect_count':total-good_count,'yield_percent':good_count/total*100 if total else 0.0,'bins':bins,'defects_by_zone':defects_by_zone,'defects_by_bin':defects_by_bin,'tested_zones':zones}

def lot_route_metrics(route:dict[str,Any],*,started_at:datetime|None=None,now:datetime|None=None)->dict[str,Any]:
    steps=route.get('steps',[]) if isinstance(route,dict) else []
    if not isinstance(steps,list):raise ValueError('Lot route must contain a steps list.')
    completed=sum(1 for step in steps if str(step.get('status','')).lower() in {'done','complete','completed','passed'});current=next((step for step in steps if str(step.get('status','')).lower() in {'running','hold','held','in_progress'}),None)
    queue_minutes=sum(max(0.0,float(step.get('queue_minutes',0) or 0)) for step in steps);now=now or datetime.now(timezone.utc);cycle_minutes=0.0
    if started_at is not None:
        if started_at.tzinfo is None:started_at=started_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:now=now.replace(tzinfo=timezone.utc)
        if now<started_at:raise ValueError('Route observation time must not precede start.')
        cycle_minutes=(now-started_at).total_seconds()/60
    return {'step_count':len(steps),'completed_steps':completed,'progress_percent':completed/len(steps)*100 if steps else 0.0,'current_step':current.get('name') if current else None,'on_hold':bool(current and str(current.get('status','')).lower() in {'hold','held'}),'queue_minutes':queue_minutes,'cycle_minutes':cycle_minutes,'wip':bool(steps and completed<len(steps))}

def equipment_reliability(states:list[dict[str,Any]],*,planned_minutes:float|None=None,ideal_cycle_minutes:float|None=None,total_units:float|None=None,good_units:float|None=None)->dict[str,Any]:
    durations=[max(0.0,float(state.get('duration_minutes',0) or 0)) for state in states];total=sum(durations);down=sum(duration for duration,state in zip(durations,states) if str(state.get('state','')).lower() in {'unscheduled_down','failure','down'});production=sum(duration for duration,state in zip(durations,states) if str(state.get('state','')).lower() in {'production','run','running'});failures=sum(1 for state in states if str(state.get('state','')).lower() in {'unscheduled_down','failure','down'});availability=production/(planned_minutes or total) if (planned_minutes or total) else 0.0;mtbf=production/failures if failures else None;mttr=down/failures if failures else None
    performance=None;quality=None;oee=None
    if ideal_cycle_minutes is not None and total_units is not None and planned_minutes:
        performance=(ideal_cycle_minutes*total_units)/(production or planned_minutes)
    if total_units is not None and good_units is not None and total_units>0:quality=good_units/total_units
    if performance is not None and quality is not None:oee=availability*performance*quality
    return {'total_minutes':total,'production_minutes':production,'downtime_minutes':down,'availability':availability,'mtbf_minutes':mtbf,'mttr_minutes':mttr,'performance':performance,'quality':quality,'oee':oee}

def genealogy_graph(events:list[dict[str,Any]])->dict[str,Any]:
    edges:set[tuple[str,str]]=set();nodes:set[str]=set()
    for event in events:
        parents=[str(value) for value in event.get('parent_ids',[])];children=[str(value) for value in event.get('child_ids',[])]
        if not parents or not children:continue
        nodes.update(parents);nodes.update(children);edges.update((parent,child) for parent in parents for child in children if parent!=child)
    adjacency={node:[] for node in nodes}
    for parent,child in edges:adjacency[parent].append(child)
    visiting:set[str]=set();visited:set[str]=set()
    def visit(node:str)->None:
        if node in visiting:raise ValueError('Lot genealogy must be acyclic.')
        if node in visited:return
        visiting.add(node)
        for child in adjacency[node]:visit(child)
        visiting.remove(node);visited.add(node)
    for node in nodes:visit(node)
    return {'nodes':sorted(nodes),'edges':[{'parent_id':parent,'child_id':child} for parent,child in sorted(edges)]}

def capacity_metrics(demand_units:float,capacity_units:float,*,shift_hours:float=8.0,shifts:int=1)->dict[str,float|bool]:
    if demand_units<0 or capacity_units<=0 or shift_hours<=0 or shifts<1:raise ValueError('Capacity inputs are invalid.')
    planned=capacity_units*shifts;return {'demand_units':demand_units,'capacity_units':planned,'utilization_percent':demand_units/planned*100,'shortfall_units':max(0.0,demand_units-planned),'bottleneck':demand_units>planned}
