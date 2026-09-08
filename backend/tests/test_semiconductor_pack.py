from datetime import datetime,timezone,timedelta
import pytest
from app.packs.semiconductor.models import normalize_equipment_state,normalize_lot,normalize_wafer,recipe_diff


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
