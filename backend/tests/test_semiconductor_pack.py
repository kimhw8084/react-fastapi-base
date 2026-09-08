from datetime import datetime,timezone,timedelta
import pytest
from app.packs.semiconductor.models import capacity_metrics,equipment_reliability,genealogy_graph,lot_route_metrics,normalize_equipment_state,normalize_lot,normalize_wafer,recipe_diff,wafer_defect_summary


def test_wafer_summary_and_validation():
    result=normalize_wafer({'die_rows':2,'die_cols':3,'bin_map':{'good_bins':['1'],'cells':[{'x':0,'y':0,'bin':'1'},{'x':1,'y':0,'bin':'2','defect':'scratch'},{'x':2,'y':1,'bin':'1'}]}})
    assert result['total_die']==3 and result['good_die']==2 and result['defect_count']==1
    assert result['yield_percent']==pytest.approx(66.6666667)
    with pytest.raises(ValueError):normalize_wafer({'die_rows':2,'die_cols':2,'bin_map':{'cells':[{'x':2,'y':0,'bin':'1'}]}})
    with pytest.raises(ValueError):normalize_wafer({'die_rows':2,'die_cols':2,'bin_map':{'cells':[{'x':0,'y':0,'bin':'1'},{'x':0,'y':0,'bin':'2'}]}})


def test_lot_route_equipment_state_and_recipe_diff():
    start=datetime(2026,9,7,12,tzinfo=timezone.utc)
    lot=normalize_lot({'route':{'steps':[{'id':'etch','name':'Etch'},{'id':'met','name':'Metrology'}]},'started_at':start,'target_complete':start+timedelta(hours=5)})
    assert [step['id'] for step in lot['route']['steps']]==['etch','met']
    with pytest.raises(ValueError):normalize_lot({'route':{'steps':[{'id':'x','name':'One'},{'id':'x','name':'Two'}]},'started_at':start,'target_complete':start})
    state=normalize_equipment_state({'started_at':start,'ended_at':start+timedelta(minutes=90)})
    assert state['duration_minutes']==90
    with pytest.raises(ValueError):normalize_equipment_state({'started_at':start,'ended_at':start-timedelta(minutes=1)})
    assert recipe_diff({'pressure':10,'temp':100},{'pressure':12,'temp':100,'gas':'Ar'})==[{'key':'gas','before':None,'after':'Ar'},{'key':'pressure','before':10,'after':12}]

def test_derived_metrics_cover_yield_genealogy_route_reliability_and_capacity():
    summary=wafer_defect_summary([{'x':0,'y':0,'bin':'1'},{'x':1,'y':1,'bin':'2'},{'x':2,'y':2,'bin':'1'}],rows=3,cols=3,good_bins=('1',),edge_exclusion=1)
    assert summary['good_die']==2 and summary['defects_by_zone']=={'edge':0,'center':1}
    route=lot_route_metrics({'steps':[{'name':'Etch','status':'done'},{'name':'Metrology','status':'hold','queue_minutes':12}]},started_at=datetime(2026,9,7,12,tzinfo=timezone.utc),now=datetime(2026,9,7,14,tzinfo=timezone.utc))
    assert route['on_hold'] and route['queue_minutes']==12 and route['progress_percent']==50
    graph=genealogy_graph([{'parent_ids':['L1'],'child_ids':['L2','L3']}])
    assert graph['edges']==[{'parent_id':'L1','child_id':'L2'},{'parent_id':'L1','child_id':'L3'}]
    reliability=equipment_reliability([{'state':'production','duration_minutes':90},{'state':'unscheduled_down','duration_minutes':30}],planned_minutes=120)
    assert reliability['mtbf_minutes']==90 and reliability['mttr_minutes']==30
    assert capacity_metrics(120,100,shifts=1)['bottleneck'] is True
