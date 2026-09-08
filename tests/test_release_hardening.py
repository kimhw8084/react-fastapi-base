from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def run(*args,env=None):
    return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,env=env or os.environ.copy(),timeout=30)

def test_security_source_gate_passes_repository():
    result=run(sys.executable,'scripts/security_source_check.py')
    assert result.returncode==0,result.stdout+result.stderr
    assert 'Security source checks passed' in result.stdout

def test_performance_gate_writes_machine_readable_report(tmp_path):
    env=os.environ.copy();env['BASE_PERFORMANCE_REPORT']=str(tmp_path/'performance.json')
    result=run(sys.executable,'scripts/performance_check.py',env=env)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads((tmp_path/'performance.json').read_text())
    assert report['browser_render_budget_certified'] is False
    assert len(report['checks'])>=10
    assert {check['name'] for check in report['checks']} >= {
        'descriptive-100k',
        'imr-100k',
        'ewma-100k',
        'run-rules-100k',
        'pareto-100k',
        'p-chart-100k',
        'c-chart-100k',
        'cusum-100k',
        'correlation-100k',
        'regression-100k',
    }
    assert all(row['status']=='PASS' and row['seconds']<=row['budget_seconds'] for row in report['checks'])

def test_implementation_evidence_only_references_real_roadmap_and_sources():
    roadmap=json.loads((ROOT/'catalog/roadmap.json').read_text())['entries']
    known={row['id'] for row in roadmap}
    evidence=json.loads((ROOT/'catalog/implementation-evidence.json').read_text())
    assert evidence['stable_promotions_by_this_script']==0
    assert len(evidence['entries'])>=250
    for row in evidence['entries']:
        assert row['id'] in known
        assert (ROOT/row['source']).is_file()
        assert row['implementation_status']=='implemented-source'
        assert row['release_maturity']!='stable'
