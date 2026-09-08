#!/usr/bin/env python3
"""Safely register a typed relationship between canonical entities.

Dry-run is the default. The generic relationship table stores relationship
instances, so adding a relationship type does not require a database migration.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,tempfile
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
KEY=re.compile(r'^[a-z][a-z0-9_]{0,59}$')
ENTITY=re.compile(r'^[a-z][a-z0-9_]{0,39}$')
CARDINALITIES={'one_to_one','one_to_many','many_to_one','many_to_many'}
KINDS={'reference','hierarchy','dependency','placement','causal','temporal','logical','connection'}
ALLOWED={'key','label','source_entity','target_entity','forward_label','reverse_label','cardinality','kind','placement_capacity','allow_self','acyclic','allow_parallel'}

def atomic(path:Path,content:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:handle.write(content)
        os.replace(name,path)
    finally:
        try:os.unlink(name)
        except FileNotFoundError:pass

def validate(payload:dict[str,Any],entities:set[str])->dict[str,Any]:
    if not isinstance(payload,dict):raise ValueError('Relationship spec must be an object.')
    unknown=set(payload)-ALLOWED
    if unknown:raise ValueError('Unknown relationship spec keys: '+', '.join(sorted(unknown)))
    missing={'key','label','source_entity','target_entity','forward_label','reverse_label'}-set(payload)
    if missing:raise ValueError('Missing relationship spec keys: '+', '.join(sorted(missing)))
    key=payload['key'];source=payload['source_entity'];target=payload['target_entity']
    if not isinstance(key,str) or not KEY.fullmatch(key):raise ValueError('Relationship key must be lower snake_case.')
    if not isinstance(source,str) or not ENTITY.fullmatch(source) or source not in entities:raise ValueError('source_entity must name a registered canonical entity.')
    if not isinstance(target,str) or not ENTITY.fullmatch(target) or target not in entities:raise ValueError('target_entity must name a registered canonical entity.')
    cardinality=payload.get('cardinality','many_to_many')
    if cardinality not in CARDINALITIES:raise ValueError('Unsupported relationship cardinality.')
    kind=payload.get('kind','reference')
    if kind not in KINDS:raise ValueError('Unsupported relationship kind.')
    placement_capacity=payload.get('placement_capacity')
    if kind=='placement':
        if source==target:raise ValueError('Placement source and target entities must differ.')
        if isinstance(placement_capacity,bool) or not isinstance(placement_capacity,int) or not 1<=placement_capacity<=1000:raise ValueError('Placement relationships require placement_capacity from 1 to 1000.')
    elif placement_capacity is not None:raise ValueError('placement_capacity is only valid for placement relationships.')
    result={'key':key}
    for name in ('label','forward_label','reverse_label'):
        value=payload[name]
        if not isinstance(value,str) or not 1<=len(value.strip())<=120:raise ValueError(f'{name} must be 1-120 characters.')
        result[name]=value.strip()
    result.update(source_entity=source,target_entity=target,cardinality=cardinality,kind=kind,placement_capacity=placement_capacity,allow_self=bool(payload.get('allow_self',False)),acyclic=bool(payload.get('acyclic',False)),allow_parallel=bool(payload.get('allow_parallel',False)))
    return result

def generate(root:Path,payload:dict[str,Any],apply:bool=False)->dict[str,Any]:
    root=root.resolve()
    manifest_path=root/'backend/app/features/manifest.json'
    config_path=root/'backend/app/config/relationships.json'
    entities=set(json.loads(manifest_path.read_text()))
    spec=validate(payload,entities)
    current=json.loads(config_path.read_text()) if config_path.exists() else []
    if not isinstance(current,list):raise ValueError('Relationship configuration must be a list.')
    if any(item.get('key')==spec['key'] for item in current if isinstance(item,dict)):raise ValueError('Relationship definition already exists.')
    # Disallow exact duplicates under a different key because they create ambiguous UI actions.
    if any(isinstance(item,dict) and item.get('source_entity')==spec['source_entity'] and item.get('target_entity')==spec['target_entity'] and item.get('forward_label')==spec['forward_label'] and item.get('reverse_label')==spec['reverse_label'] for item in current):
        raise ValueError('An equivalent relationship definition already exists.')
    updated=[*current,spec]
    content=json.dumps(updated,indent=2)+'\n'
    plan={'relationship':spec,'config':'backend/app/config/relationships.json','before_sha256':hashlib.sha256(config_path.read_bytes()).hexdigest() if config_path.exists() else None,'after_sha256':hashlib.sha256(content.encode()).hexdigest(),'database_migration_required':False}
    if apply:atomic(config_path,content)
    return plan

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec',type=Path)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    plan=generate(args.root,json.loads(args.spec.read_text()),args.apply)
    print(json.dumps(plan,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
