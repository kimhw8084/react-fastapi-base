#!/usr/bin/env python3
"""Generate the catalog from the compiled registry; completeness is never inferred from presence."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from generate_catalog_registry import render as render_registry
def outputs():
    result=subprocess.run(['node','--input-type=module','-e',"import {catalog} from './experience-lab/public/lib/registry.js'; console.log(JSON.stringify(catalog))"],cwd=ROOT,text=True,capture_output=True,check=True)
    entries=json.loads(result.stdout)
    if len({r['tag'] for r in entries})!=len(entries):raise ValueError('Duplicate widget tags inflate catalog coverage.')
    for row in entries:
        source=ROOT/'experience-lab/src'/row['source']
        if not source.is_file():raise ValueError('Missing source: '+str(source))
        row.update(maturity='implemented-provisional',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),react_host_verified=False,production_certified=False)
    obj={'schema_version':1,'unique_interactive_families':len(entries),'entries':entries,'note':'These are local model-controlled widgets. Tests do not certify React integration, production data, or the complete roadmap.'}
    roadmap=json.loads((ROOT/'catalog/roadmap.json').read_text())
    text=['# Component and platform coverage','','This is an explicit delivery ledger, not a percentage-complete claim.','','## Interactive families','','| Family | Capabilities | Remaining limits |','|---|---|---|']
    for row in entries:text.append(f"| {row['title']} | {'; '.join(row['capabilities'])} | {'; '.join(row['limits'])} |")
    text+=['','## Full retained scope','','All entries remain required until explicitly approved otherwise. `partial` means a demonstration covers part of the contract, not a certified reusable implementation.','','| Required item | Category | Status | Related examples |','|---|---|---|---|']
    for row in roadmap['entries']:text.append(f"| {row['id']} | {row['category']} | {row['maturity']} | {', '.join(row['demo_families']) or '—'} |")
    return {
        ROOT/'catalog/components.json':json.dumps(obj,indent=2)+'\n',
        ROOT/'docs/COMPONENT_COVERAGE.md':'\n'.join(text)+'\n',
        ROOT/'frontend/src/platform/catalog/generatedVariants.ts':render_registry(),
    }
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--release',action='store_true');a=p.parse_args()
    for path,text in outputs().items():
        if a.check:
            if not path.is_file() or path.read_text()!=text:raise SystemExit('Catalog drift: '+str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    roadmap=json.loads((ROOT/'catalog/roadmap.json').read_text());remaining=[r for r in roadmap['entries'] if r['required'] and r['maturity']!='stable']
    print(f"Catalog is current. {len(remaining)} required inventory entries are not fully certified.")
    if a.release and remaining:raise SystemExit(1)
if __name__=='__main__':main()
