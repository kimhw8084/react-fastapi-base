#!/usr/bin/env python3
"""Deterministic local performance budgets for algorithms owned by the template.

The budgets are intentionally generous enough for shared CI runners while still
catching accidental quadratic behavior. Browser/render budgets remain a separate
release gate once the dependency-resolved frontend is available.
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.platform.statistics import descriptive, imr, ewma, pareto, run_rule_flags


def timed(name, budget, fn):
    start=time.perf_counter(); result=fn(); elapsed=time.perf_counter()-start
    if elapsed>budget: raise AssertionError(f'{name} exceeded budget: {elapsed:.3f}s > {budget:.3f}s')
    print(f'PASS {name}: {elapsed:.3f}s <= {budget:.3f}s')
    return {'name':name,'seconds':elapsed,'budget_seconds':budget,'status':'PASS','summary':result}


def main()->int:
    # Deterministic finite workload: 100k observations exercises statistics without random noise.
    values=[100.0 + ((i%97)-48)*0.013 + ((i%7)-3)*0.002 for i in range(100_000)]
    categories=[f'DEFECT-{i%17:02d}' for i in range(100_000)]
    rows=[]
    rows.append(timed('descriptive-100k',1.50,lambda: descriptive(values)['count']))
    rows.append(timed('imr-100k',2.50,lambda: len(imr(values)['moving_ranges'])))
    rows.append(timed('ewma-100k',1.50,lambda: len(ewma(values))))
    rows.append(timed('run-rules-100k',2.50,lambda: sum(len(v) for v in run_rule_flags(values).values())))
    rows.append(timed('pareto-100k',1.50,lambda: len(pareto(categories))))
    output=Path(os.environ.get('BASE_PERFORMANCE_REPORT',ROOT/'.evidence/performance.json'))
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps({'schema_version':1,'scope':'owned-pure-algorithms','browser_render_budget_certified':False,'checks':rows},indent=2)+'\n')
    print('Performance smoke passed. Browser rendering and target-Mac budgets still require the dependency-resolved application build.')
    return 0

if __name__=='__main__': raise SystemExit(main())
