from datetime import datetime,timezone,timedelta
import pytest
from app.packs.software_engineering.models import normalize_delivery,normalize_incident,normalize_observability,normalize_slo

def test_delivery_incident_slo_and_observability_normalizers():
    start=datetime(2026,9,7,12,tzinfo=timezone.utc)
    delivery=normalize_delivery({'started_at':start,'completed_at':start+timedelta(minutes=12),'stages':{'items':[{'id':'build','name':'Build','status':'passed'}]}})
    assert delivery['duration_minutes']==12 and delivery['stages']['items'][0]['id']=='build'
    incident=normalize_incident({'started_at':start,'resolved_at':start+timedelta(minutes=30),'timeline':{'events':[{'kind':'detected','message':'Alert fired'}]}})
    assert incident['duration_minutes']==30 and incident['timeline']['events'][0]['kind']=='detected'
    slo=normalize_slo({'target_percent':99.9,'current_percent':99.95})
    assert slo['error_budget_remaining']==pytest.approx(50) and slo['burn_rate']==pytest.approx(.5) and slo['status']=='healthy'
    exhausted=normalize_slo({'target_percent':99.9,'current_percent':99.8})
    assert exhausted['status']=='exhausted' and exhausted['error_budget_remaining']==0
    assert normalize_observability({'duration_ms':12.4})['duration_ms']==12.4
    with pytest.raises(ValueError):normalize_observability({'duration_ms':-1})
