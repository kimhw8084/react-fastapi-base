#!/usr/bin/env python3
"""Generate a canonical entity and reusable workspace projections from JSON.

Dry-run is the default. Generated features delegate query, revision/lifecycle,
audit and relationship behavior to platform services rather than copying those
invariants into each application feature.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
KEY=re.compile(r'^[a-z][a-z0-9_]{0,39}$')
FIELD=re.compile(r'^[a-z][a-z0-9_]{0,39}$')
STRING_TYPES={'text','textarea','select','email','url','markdown','code'}
NUMERIC_TYPES={'integer','number','percent','duration','scientific','unit_number'}
STRUCTURED_TYPES={'json','multiselect'}
ALLOWED_TYPES=STRING_TYPES|NUMERIC_TYPES|STRUCTURED_TYPES|{'boolean','date','datetime'}
ALLOWED_VISUALIZATIONS={'table','board','timeline','calendar','gantt','dashboard','graph','rack'}
RESERVED={'id','revision','archived','created_by','created_at','updated_at','metadata','registry'}
FIELD_KEYS={'key','label','type','required','max_length','choices','default','searchable','filterable','column','sortable','minimum','maximum','step','unit','read_only'}


def pascal(value:str)->str:return ''.join(part[:1].upper()+part[1:] for part in value.split('_'))
def py_string(value:str)->str:return repr(value)
def ts_string(value:str)->str:return json.dumps(value)
def sql_string(value:str)->str:return "'"+value.replace("'","''")+"'"

def atomic(path:Path,content:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:handle.write(content)
        os.replace(name,path)
    finally:
        try:os.unlink(name)
        except FileNotFoundError:pass


def _validate_default(kind:str,value:Any,field:dict[str,Any])->Any:
    label=field['key']
    if kind in STRING_TYPES:
        if not isinstance(value,str):raise ValueError(f'Default for {label} must be a string.')
        if len(value)>field['max_length']:raise ValueError(f'Default for {label} is too long.')
        if kind=='select' and value not in field['choices']:raise ValueError(f'Default for {label} must be one of its choices.')
        return value
    if kind=='multiselect':
        if not isinstance(value,list) or any(not isinstance(item,str) for item in value) or len(set(value))!=len(value):raise ValueError(f'Default for {label} must be a unique list of choices.')
        if any(item not in field['choices'] for item in value):raise ValueError(f'Default for {label} contains an unsupported choice.')
        return value
    if kind=='json':
        if not isinstance(value,dict):raise ValueError(f'Default for {label} must be a JSON object.')
        if len(json.dumps(value,separators=(',',':')).encode('utf-8'))>field['max_length']:raise ValueError(f'Default for {label} is too large.')
        return value
    if kind=='integer':
        if isinstance(value,bool) or not isinstance(value,int):raise ValueError(f'Default for {label} must be an integer.')
    elif kind in {'number','percent','duration','scientific','unit_number'}:
        if isinstance(value,bool) or not isinstance(value,(int,float)):raise ValueError(f'Default for {label} must be numeric.')
        value=float(value)
    elif kind=='boolean':
        if not isinstance(value,bool):raise ValueError(f'Default for {label} must be boolean.')
    elif kind=='date':
        if not isinstance(value,str):raise ValueError(f'Default for {label} must be an ISO date string.')
        try:date.fromisoformat(value)
        except ValueError as error:raise ValueError(f'Default for {label} must be an ISO date string.') from error
    elif kind=='datetime':
        if not isinstance(value,str):raise ValueError(f'Default for {label} must be an ISO date-time string.')
        try:parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError as error:raise ValueError(f'Default for {label} must be an ISO date-time string.') from error
        if parsed.tzinfo is None:raise ValueError(f'Default for {label} must include an explicit time-zone offset.')
    if kind in NUMERIC_TYPES:
        minimum=field['minimum'];maximum=field['maximum']
        if minimum is not None and value<minimum:raise ValueError(f'Default for {label} is below minimum.')
        if maximum is not None and value>maximum:raise ValueError(f'Default for {label} is above maximum.')
    return value


def validate(payload:dict[str,Any])->dict[str,Any]:
    if not isinstance(payload,dict):raise ValueError('Entity spec must be an object.')
    allowed={'key','label','singular','description','primary_field','fields','visualizations'}
    unknown=set(payload)-allowed
    if unknown:raise ValueError('Unknown entity spec keys: '+', '.join(sorted(unknown)))
    key=payload.get('key');label=payload.get('label');singular=payload.get('singular');description=payload.get('description','')
    if not isinstance(key,str) or not KEY.fullmatch(key):raise ValueError('Entity key must be lower snake_case.')
    if not isinstance(label,str) or not 1<=len(label.strip())<=120:raise ValueError('Entity label must be 1-120 characters.')
    if not isinstance(singular,str) or not 1<=len(singular.strip())<=80:raise ValueError('Entity singular label must be 1-80 characters.')
    if not isinstance(description,str) or len(description)>500:raise ValueError('Description is too long.')
    fields=payload.get('fields')
    if not isinstance(fields,list) or not fields or len(fields)>30:raise ValueError('Entity must define 1-30 fields.')
    normalized=[];seen=set()
    for raw in fields:
        if not isinstance(raw,dict):raise ValueError('Each field must be an object.')
        extra=set(raw)-FIELD_KEYS
        if extra:raise ValueError('Unknown field keys: '+', '.join(sorted(extra)))
        fkey=raw.get('key');flabel=raw.get('label');kind=raw.get('type','text')
        if not isinstance(fkey,str) or not FIELD.fullmatch(fkey) or fkey in RESERVED:raise ValueError(f'Invalid field key: {fkey!r}')
        if fkey in seen:raise ValueError('Field keys must be unique.')
        seen.add(fkey)
        if not isinstance(flabel,str) or not 1<=len(flabel.strip())<=120:raise ValueError(f'Field {fkey} needs a label.')
        if kind not in ALLOWED_TYPES:raise ValueError(f'Unsupported field type: {kind}')
        required=bool(raw.get('required',False))
        if required and 'default' in raw:raise ValueError(f'Required field {fkey} cannot also declare a default.')
        if kind in STRING_TYPES:
            default_max=100000 if kind=='code' else 50000 if kind=='markdown' else 10000 if kind=='textarea' else 80 if kind=='select' else 160
            max_length=raw.get('max_length',default_max)
            if not isinstance(max_length,int) or not 1<=max_length<=100000:raise ValueError(f'Invalid max_length for {fkey}.')
        elif kind=='json':
            max_length=raw.get('max_length',50000)
            if not isinstance(max_length,int) or not 2<=max_length<=500000:raise ValueError(f'Invalid max_length for {fkey}.')
        elif kind=='multiselect':
            max_length=raw.get('max_length',80)
            if not isinstance(max_length,int) or not 1<=max_length<=500:raise ValueError(f'Invalid max_length for {fkey}.')
        else:
            if 'max_length' in raw:raise ValueError(f'max_length is only valid for string, JSON or multiselect fields ({fkey}).')
            max_length=None
        choices=raw.get('choices',[])
        if kind in {'select','multiselect'}:
            if not isinstance(choices,list) or not 1<=len(choices)<=100 or any(not isinstance(x,str) or not x or len(x)>max_length for x in choices) or len(set(choices))!=len(choices):raise ValueError(f'{kind} field {fkey} needs unique string choices within max_length.')
        elif choices:raise ValueError(f'Choices are only valid for select/multiselect fields ({fkey}).')
        minimum=raw.get('minimum');maximum=raw.get('maximum');step=raw.get('step')
        if kind=='percent':
            minimum=0 if minimum is None else minimum;maximum=100 if maximum is None else maximum
        if kind=='duration' and minimum is None:minimum=0
        if kind not in NUMERIC_TYPES and any(value is not None for value in (minimum,maximum,step)):raise ValueError(f'Numeric bounds are only valid for numeric fields ({fkey}).')
        for name,value in [('minimum',minimum),('maximum',maximum),('step',step)]:
            if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float))):raise ValueError(f'{name} for {fkey} must be numeric.')
        if minimum is not None and maximum is not None and minimum>maximum:raise ValueError(f'minimum cannot exceed maximum for {fkey}.')
        if step is not None and step<=0:raise ValueError(f'step must be positive for {fkey}.')
        unit=raw.get('unit')
        if kind=='percent':unit='%' if unit is None else unit
        if kind=='duration':unit='s' if unit is None else unit
        if unit is not None:
            if kind not in NUMERIC_TYPES:raise ValueError(f'Units are only valid for numeric fields ({fkey}).')
            if not isinstance(unit,str) or not 1<=len(unit.strip())<=24:raise ValueError(f'Invalid unit for {fkey}.')
            unit=unit.strip()
        if kind=='unit_number' and not unit:raise ValueError(f'unit_number field {fkey} requires unit.')
        searchable=bool(raw.get('searchable',kind in {'text','textarea','email','url','markdown','code'}))
        if searchable and kind not in STRING_TYPES:raise ValueError(f'Only string fields can be searchable ({fkey}).')
        filterable=bool(raw.get('filterable',kind in {'select','boolean'}))
        if filterable and kind not in {'select','boolean'}:raise ValueError(f'Generated filters currently support select/boolean fields only ({fkey}).')
        default_present='default' in raw
        default=raw.get('default')
        nullable=not required and not default_present
        complex_kind=kind in {'textarea','markdown','code','json','multiselect'}
        field={'key':fkey,'label':flabel.strip(),'type':kind,'required':required,'nullable':nullable,'max_length':max_length,'choices':choices,'minimum':minimum,'maximum':maximum,'step':step,'unit':unit,'read_only':bool(raw.get('read_only',False)),'searchable':searchable,'filterable':filterable,'column':bool(raw.get('column',not complex_kind)),'sortable':bool(raw.get('sortable',not complex_kind and kind!='multiselect')),'default_present':default_present,'default':None}
        if default_present:field['default']=_validate_default(kind,default,field)
        normalized.append(field)
    primary=payload.get('primary_field',normalized[0]['key'])
    if primary not in {x['key'] for x in normalized}:raise ValueError('primary_field must name a declared field.')
    primary_field=next(x for x in normalized if x['key']==primary)
    if primary_field['type'] not in {'text','select','email','url'}:raise ValueError('primary_field must be a short string/select field suitable for record identity.')
    visualizations=payload.get('visualizations',['table'])
    if not isinstance(visualizations,list) or not visualizations or len(visualizations)>len(ALLOWED_VISUALIZATIONS):raise ValueError('visualizations must contain at least one supported projection.')
    if any(not isinstance(value,str) or value not in ALLOWED_VISUALIZATIONS for value in visualizations) or len(set(visualizations))!=len(visualizations):raise ValueError('Unsupported or duplicate visualization.')
    return {'key':key,'label':label.strip(),'singular':singular.strip(),'description':description.strip(),'primary_field':primary,'fields':normalized,'visualizations':visualizations}


def _py_type(field:dict[str,Any])->str:
    return {'text':'str','textarea':'str','select':'str','email':'str','url':'str','markdown':'str','code':'str','json':'dict[str,Any]','multiselect':'list[str]','integer':'int','number':'float','percent':'float','duration':'float','scientific':'float','unit_number':'float','boolean':'bool','date':'date','datetime':'datetime'}[field['type']]

def _sa_type(field:dict[str,Any],prefix='')->str:
    name={'text':'String','textarea':'String','select':'String','email':'String','url':'String','markdown':'String','code':'String','json':'JSON','multiselect':'JSON','integer':'Integer','number':'Float','percent':'Float','duration':'Float','scientific':'Float','unit_number':'Float','boolean':'Boolean','date':'Date','datetime':'DateTime'}[field['type']]
    if name=='String':return f'{prefix}String({field["max_length"]})'
    if name=='DateTime':return f'{prefix}DateTime(timezone=True)'
    return f'{prefix}{name}'

def _py_default(field:dict[str,Any])->str:
    value=field['default']
    if field['type']=='date':return f'date.fromisoformat({value!r})'
    if field['type']=='datetime':return f'datetime.fromisoformat({value!r}.replace("Z","+00:00"))'
    return repr(value)


def model_source(spec:dict[str,Any])->str:
    cls=pascal(spec['key'].rstrip('s') or spec['key'])
    columns=[];constraints=[]
    for f in spec['fields']:
        pytype=_py_type(f)+(' | None' if f['nullable'] else '')
        args=[_sa_type(f),f'nullable={f["nullable"]}']
        if f['nullable']:args.append('default=None')
        elif f['default_present']:args.append(f'default={_py_default(f)}')
        if f['sortable'] or f['filterable']:args.append('index=True')
        columns.append(f"    {f['key']}: Mapped[{pytype}]=mapped_column({','.join(args)})")
        if f['type']=='select':constraints.append(f"      CheckConstraint({(f['key']+' IN ('+','.join(sql_string(x) for x in f['choices'])+')')!r},name={('ck_'+spec['key']+'_'+f['key'])!r}),")
        if f['required'] and f['type'] in STRING_TYPES:constraints.append(f"      CheckConstraint({('length(trim('+f['key']+')) BETWEEN 1 AND '+str(f['max_length']))!r},name={('ck_'+spec['key']+'_'+f['key']+'_required')!r}),")
        if f['minimum'] is not None:constraints.append(f"      CheckConstraint({(f['key']+' >= '+str(f['minimum']))!r},name={('ck_'+spec['key']+'_'+f['key']+'_minimum')!r}),")
        if f['maximum'] is not None:constraints.append(f"      CheckConstraint({(f['key']+' <= '+str(f['maximum']))!r},name={('ck_'+spec['key']+'_'+f['key']+'_maximum')!r}),")
    constraints.append(f"      CheckConstraint('revision >= 1',name={('ck_'+spec['key']+'_revision')!r}),")
    return f'''from datetime import date,datetime\nfrom typing import Any\nfrom sqlalchemy import Boolean,CheckConstraint,Date,DateTime,Float,Integer,JSON,String\nfrom sqlalchemy.orm import Mapped,mapped_column\nfrom app.platform.models import TenantBase,utcnow\n\nclass {cls}(TenantBase):\n    __tablename__={spec['key']!r}\n    id: Mapped[str]=mapped_column(String(36),primary_key=True)\n'''+"\n".join(columns)+f'''\n    revision: Mapped[int]=mapped_column(Integer,default=1)\n    archived: Mapped[bool]=mapped_column(Boolean,default=False,index=True)\n    created_by: Mapped[str]=mapped_column(String(200))\n    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)\n    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)\n    __table_args__=(\n'''+"\n".join(constraints)+"\n    )\n"


def schemas_source(spec:dict[str,Any])->str:
    singular=pascal(spec['key'].rstrip('s') or spec['key'])
    lines=[];validators=[]
    for f in spec['fields']:
        if f['type']=='select':base='Literal['+','.join(repr(x) for x in f['choices'])+']'
        elif f['type']=='multiselect':base='list[Literal['+','.join(repr(x) for x in f['choices'])+']]'
        else:base=_py_type(f)
        type_expr=base+(' | None' if f['nullable'] else '')
        args=[]
        if f['nullable']:args.append('default=None')
        elif f['default_present']:args.append('default='+_py_default(f))
        if f['type'] in STRING_TYPES:
            if f['required']:args.append('min_length=1')
            args.append(f"max_length={f['max_length']}")
        if f['type']=='multiselect':
            if f['required']:args.append('min_length=1')
            args.append('max_length=100')
        if f['minimum'] is not None:args.append(f"ge={f['minimum']!r}")
        if f['maximum'] is not None:args.append(f"le={f['maximum']!r}")
        lines.append(f"    {f['key']}: {type_expr}=Field({','.join(args)})")
        if f['type']=='json':
            validators.extend([
                f"    @field_validator({f['key']!r})",
                '    @classmethod',
                f"    def validate_{f['key']}_size(cls,value):",
                f"        if value is not None and len(json.dumps(value,separators=(',',':')).encode('utf-8'))>{f['max_length']}:raise ValueError('JSON object exceeds {f['max_length']} bytes.')",
                '        return value',
            ])
    body='\n'.join(lines)
    validation='\n'.join(validators)
    if validation:validation+='\n'
    return f'''from datetime import date,datetime
from typing import Any,Literal
import json
from pydantic import Field,field_validator
from app.platform.schemas import StrictSchema

class {singular}Create(StrictSchema):
{body}
{validation}    @field_validator('*')
    @classmethod
    def trim_strings(cls,value):return value.strip() if isinstance(value,str) else value
class {singular}Update({singular}Create):
    revision:int=Field(ge=1)
class {singular}Read({singular}Create):
    id:str;revision:int;archived:bool;created_by:str;created_at:datetime;updated_at:datetime
class {singular}Page(StrictSchema):
    items:list[{singular}Read];total:int;limit:int;offset:int
class BulkTarget(StrictSchema):
    id:str;revision:int=Field(ge=1)
class {singular}BulkRequest(StrictSchema):
    action:Literal['archive','restore'];targets:list[BulkTarget]=Field(min_length=1,max_length=100)
class RevertRequest(StrictSchema):
    revision:int=Field(ge=1);target_revision:int=Field(ge=1)
'''


def definition_source(spec:dict[str,Any])->str:
    fields=",\n        ".join(f"FieldDefinition(key={f['key']!r},label={f['label']!r},kind={f['type']!r},required={f['required']},nullable={f['nullable']},max_length={f['max_length']!r},choices={f['choices']!r},minimum={f['minimum']!r},maximum={f['maximum']!r},step={f['step']!r},unit={f['unit']!r},read_only={f['read_only']})" for f in spec['fields'])
    filters=[f['key'] for f in spec['fields'] if f['filterable']]
    sorts=[f['key'] for f in spec['fields'] if f['sortable']]+['updated_at','created_at','created_by','revision']
    columns=[f['key'] for f in spec['fields'] if f['column']]+['updated_at','revision']
    capabilities=['search','filters','sorting','selection','bulk','saved_views','details','history','compare','archive','restore','relationships']+[value for value in spec['visualizations'] if value!='table']
    return f'''from app.platform.schemas import FieldDefinition,WorkspaceDefinition\n\ndef definition()->WorkspaceDefinition:\n    return WorkspaceDefinition(key={spec['key']!r},label={spec['label']!r},description={spec['description']!r},primary_field={spec['primary_field']!r},fields=[\n        {fields}\n    ],filter_keys={filters!r},sort_keys={sorts!r},columns={columns!r},capabilities={capabilities!r},visualizations={spec['visualizations']!r})\n'''


def service_source(spec:dict[str,Any])->str:
    cls=pascal(spec['key'].rstrip('s') or spec['key']);filters=[]
    for f in spec['fields']:
        if not f['filterable']:continue
        if f['type']=='boolean':filters.append(f"{f['key']!r}:({cls}.{f['key']},('true','false'),lambda value:value=='true')")
        else:filters.append(f"{f['key']!r}:({cls}.{f['key']},{tuple(f['choices'])!r})")
    sorts=[f['key'] for f in spec['fields'] if f['sortable']]+['updated_at','created_at','created_by','revision']
    sort_src=','.join(f"{key!r}:{cls}.{key}" for key in sorts)
    search=[f"{cls}.{f['key']}" for f in spec['fields'] if f['searchable']] or [f"{cls}.{spec['primary_field']}"]
    return f'''from app.platform.errors import AppError\nfrom app.platform.query_service import EntityQueryService\nfrom app.platform.revision_service import RevisionCrudService\nfrom .models import {cls}\nfrom .schemas import {cls}Create,{cls}Read,{cls}Page,{cls}BulkRequest\nWORKSPACE={spec['key']!r}\nSORTS={{{sort_src}}}\nCRUD=RevisionCrudService(model={cls},create_schema={cls}Create,read_schema={cls}Read,workspace=WORKSPACE,not_found_label={spec['singular'].title()!r})\nQUERY=EntityQueryService(model={cls},read_schema={cls}Read,sorts=SORTS,search_columns=({','.join(search)},),filters={{{','.join(filters)}}})\ndef list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema={cls}Page,search=search,filter_values=filters or {{}},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)\ndef bulk(session,actor,data:{cls}BulkRequest):\n    if len({{x.id for x in data.targets}})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')\n    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]\n'''


def entity_source(spec:dict[str,Any])->str:
    cls=pascal(spec['key'].rstrip('s') or spec['key']);search=[f"{cls}.{f['key']}" for f in spec['fields'] if f['searchable']] or [f"{cls}.{spec['primary_field']}"]
    search_or=','.join(f"{column}.ilike(f'%{{escaped}}%',escape='\\\\')" for column in search)
    return f'''from sqlalchemy import or_,select\nfrom app.platform.entity_registry import EntityBinding\nfrom app.platform.schemas import EntityDefinition,EntityReference\nfrom .models import {cls}\nfrom . import service\ndef _ref(row):return EntityReference(entity={spec['key']!r},id=row.id,label=str(getattr(row,{spec['primary_field']!r})),workspace={spec['key']!r},archived=row.archived,revision=row.revision)\ndef resolve(session,record_id):\n    row=session.get({cls},record_id);return _ref(row) if row else None\ndef search(session,query,limit):\n    where=[]\n    if query:\n        escaped=query.replace('\\\\','\\\\\\\\').replace('%','\\\\%').replace('_','\\\\_');where.append(or_({search_or}))\n    return [_ref(row) for row in session.scalars(select({cls}).where(*where).order_by({cls}.archived,{cls}.{spec['primary_field']},{cls}.id).limit(limit)).all()]\ndef bulk_update(session,actor,targets,patch):\n    rows=service.CRUD.bulk_update(session,actor,targets,patch);return [resolve(session,row.id) for row in rows]\ndef binding():return EntityBinding(EntityDefinition(key={spec['key']!r},label={spec['label']!r},description={spec['description']!r},workspace={spec['key']!r},primary_field={spec['primary_field']!r},authority='canonical',search_fields={[f['key'] for f in spec['fields'] if f['searchable']]!r},capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)\n'''


def router_source(spec:dict[str,Any])->str:
    cls=pascal(spec['key'].rstrip('s') or spec['key']);path=spec['key'].replace('_','-');filters=[f for f in spec['fields'] if f['filterable']]
    params=''.join(f",{f['key']}:str=''" for f in filters);fd='{'+','.join(repr(f['key'])+':'+f['key'] for f in filters)+'}'
    return f'''from typing import Annotated\nfrom fastapi import APIRouter,Depends,Header,Query,Request\nfrom app.platform.idempotency import execute_once\nfrom app.platform.schemas import AuditRead,RevisionInput\nfrom app.platform.security import Actor,actor_for\nfrom app.platform.transactions import write_transaction\nfrom . import service\nfrom .schemas import {cls}Create,{cls}Update,{cls}Read,{cls}Page,{cls}BulkRequest,RevertRequest\nrouter=APIRouter(prefix={('/'+path)!r},tags=[{spec['label']!r}]);A=Annotated[Actor,Depends(actor_for)]\n@router.get('',response_model={cls}Page)\ndef list_records(request:Request,actor:A,search:str=Query('',max_length=200),archived:bool=False,sort:str='updated_at',direction:str='desc',limit:int=Query(50,ge=1,le=1000),offset:int=Query(0,ge=0){params}):\n    with request.app.state.database.session(actor.tenant_id) as db:return service.list_records(db,actor,search=search,filters={fd},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)\n@router.post('',response_model={cls}Read,status_code=201)\ndef create(request:Request,actor:A,data:{cls}Create,idempotency_key:str|None=Header(None)):\n    with write_transaction(request.app.state.database,actor.tenant_id) as db:return execute_once(db,actor,idempotency_key,{(spec['key']+'.create')!r},data.model_dump(),lambda:service.CRUD.create(db,actor,data).model_dump(mode='json'))\n@router.post('/bulk',response_model=list[{cls}Read])\ndef bulk(request:Request,actor:A,data:{cls}BulkRequest,idempotency_key:str=Header(...)):\n    with write_transaction(request.app.state.database,actor.tenant_id) as db:\n        result=execute_once(db,actor,idempotency_key,{(spec['key']+'.bulk')!r},data.model_dump(),lambda:{{'items':[row.model_dump(mode='json') for row in service.bulk(db,actor,data)]}});return result['items']\n@router.get('/{{record_id}}',response_model={cls}Read)\ndef get_record(request:Request,actor:A,record_id:str):\n    actor.require('read')\n    with request.app.state.database.session(actor.tenant_id) as db:return {cls}Read.model_validate(service.CRUD.require(db,record_id))\n@router.put('/{{record_id}}',response_model={cls}Read)\ndef update_record(request:Request,actor:A,record_id:str,data:{cls}Update):\n    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.update(db,actor,record_id,data.revision,data.model_dump(exclude={{'revision'}}))\n@router.post('/{{record_id}}/lifecycle/{{action}}',response_model={cls}Read)\ndef lifecycle(request:Request,actor:A,record_id:str,action:str,data:RevisionInput):\n    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.lifecycle(db,actor,record_id,data.revision,action)\n@router.get('/{{record_id}}/history',response_model=list[AuditRead])\ndef history(request:Request,actor:A,record_id:str):\n    with request.app.state.database.session(actor.tenant_id) as db:return service.CRUD.history(db,actor,record_id)\n@router.post('/{{record_id}}/revert',response_model={cls}Read)\ndef revert(request:Request,actor:A,record_id:str,data:RevertRequest):\n    with write_transaction(request.app.state.database,actor.tenant_id) as db:return service.CRUD.revert(db,actor,record_id,data.revision,data.target_revision)\n'''


def _draft_parse_expr(field:dict[str,Any])->str:
    key=field['key'];label=ts_string(field['label']);raw=f"String(draft.{key}??'')";kind=field['type']
    fallback='null' if field['nullable'] else json.dumps(field['default']) if field['default_present'] else 'undefined'
    if kind=='select':
        valid=json.dumps(field['choices'])
        if field['required']:return f"parseEnumDraft({raw},{label},{valid} as const)"
        return f"parseEnumDraft({raw},{label},{valid} as const,{fallback})"
    if kind in STRING_TYPES:
        if field['required']:return f"requiredStringDraft({raw},{label})"
        value=f"nullableStringDraft({raw})"
        return value if fallback=='null' else f"{value}??{fallback}"
    if kind=='integer':
        if field['required']:return f"parseIntegerDraft({raw},{label})"
        return f"{raw}.trim()?parseIntegerDraft({raw},{label}):{fallback}"
    if kind in {'number','percent','duration','scientific','unit_number'}:
        if field['required']:return f"parseNumberDraft({raw},{label})"
        return f"{raw}.trim()?parseNumberDraft({raw},{label}):{fallback}"
    if kind=='boolean':
        if field['required']:return f"parseBooleanDraft({raw})"
        return f"{raw}===''?{fallback}:parseBooleanDraft({raw})"
    if kind=='date':
        if field['required']:return f"requiredStringDraft({raw},{label})"
        return f"{raw}.trim()?{raw}:{fallback}"
    if kind=='datetime':
        if field['required']:return f"datetimeInputToIso({raw},{label})"
        return f"{raw}.trim()?datetimeInputToIso({raw},{label}):{fallback}"
    if kind=='json':
        if field['required']:return f"parseJsonObjectDraft({raw},{label})"
        return f"{raw}.trim()?parseJsonObjectDraft({raw},{label}):{fallback}"
    if kind=='multiselect':
        if field['required']:return f"parseMultiSelectDraft({raw},{label},{json.dumps(field['choices'])},true)"
        return f"{raw}.trim()?parseMultiSelectDraft({raw},{label},{json.dumps(field['choices'])},false):{fallback}"
    raise ValueError(kind)


def _draft_read_expr(field:dict[str,Any])->str:
    key=field['key'];kind=field['type']
    if kind=='datetime':
        default_value='undefined' if not field['default_present'] else ts_string(field['default'])
        return f"row?.{key}==null?datetimeToInput({default_value}):datetimeToInput(row.{key})"
    if kind=='json':
        default_value='undefined' if not field['default_present'] else json.dumps(field['default'])
        return f"row?.{key}==null?readJsonDraft({default_value}):readJsonDraft(row.{key})"
    if kind=='multiselect':
        default_value='undefined' if not field['default_present'] else json.dumps(field['default'])
        return f"row?.{key}==null?readMultiSelectDraft({default_value}):readMultiSelectDraft(row.{key})"
    new_default="''" if not field['default_present'] else ts_string(str(field['default']).lower() if isinstance(field['default'],bool) else str(field['default']))
    return f"row?.{key}==null?{new_default}:String(row.{key})"


def frontend_adapter(spec:dict[str,Any])->str:
    cls=pascal(spec['key'].rstrip('s') or spec['key']);path=spec['key'].replace('_','-')
    pairs=','.join(f"{f['key']}:{_draft_parse_expr(f)}" for f in spec['fields'])
    draft=','.join(f"{f['key']}:{_draft_read_expr(f)}" for f in spec['fields'])
    imports={'parseEnumDraft'}
    for field in spec['fields']:
        kind=field['type']
        if field['required'] and kind in STRING_TYPES:imports.add('requiredStringDraft')
        if not field['required'] and kind in STRING_TYPES:imports.add('nullableStringDraft')
        if kind=='integer':imports.add('parseIntegerDraft')
        if kind in {'number','percent','duration','scientific','unit_number'}:imports.add('parseNumberDraft')
        if kind=='boolean':imports.add('parseBooleanDraft')
        if kind=='datetime':imports.update({'datetimeInputToIso','datetimeToInput'})
        if kind=='json':imports.update({'parseJsonObjectDraft','readJsonDraft'})
        if kind=='multiselect':imports.update({'parseMultiSelectDraft','readMultiSelectDraft'})
    draft_import=','.join(sorted(imports))
    return f'''import type {{ AuditRead,{cls}Create,{cls}Page,{cls}Read,WorkspaceDefinition }} from '../../generated/schema'\nimport type {{ ApiClient }} from '../../platform/api/client'\nimport {{ {draft_import} }} from '../../platform/workspace/fieldDraft'\nimport type {{ Draft,WorkspaceAdapter }} from '../../platform/workspace/types'\nfunction parseDraft(draft:Draft):{cls}Create{{return {{{pairs}}}}}\nexport function adapter(api:ApiClient,definition:WorkspaceDefinition):WorkspaceAdapter<{cls}Read>{{const base={('/api/v1/'+path)!r};return {{key:{spec['key']!r},entityKey:{spec['key']!r},singular:{spec['singular']!r},definition,list:(query,signal)=>api.request<{cls}Page>(`${{base}}?${{new URLSearchParams(Object.entries({{...query,...query.filters,filters:undefined}}).filter(([,value])=>value!==undefined).map(([key,value])=>[key,String(value)]))}}`,{{signal}}),get:id=>api.request<{cls}Read>(`${{base}}/${{encodeURIComponent(id)}}`),create:(draft,key)=>api.json<{cls}Read>(base,'POST',parseDraft(draft),key),update:(row,draft)=>api.json<{cls}Read>(`${{base}}/${{row.id}}`,'PUT',{{...parseDraft(draft),revision:row.revision}}),transition:(row,action)=>api.json<{cls}Read>(`${{base}}/${{row.id}}/lifecycle/${{action}}`,'POST',{{revision:row.revision}}),bulk:(rows,action,key)=>api.json<{cls}Read[]>(`${{base}}/bulk`,'POST',{{action,targets:rows.map(row=>({{id:row.id,revision:row.revision}}))}},key),history:id=>api.request<AuditRead[]>(`${{base}}/${{encodeURIComponent(id)}}/history`),revert:(row,target)=>api.json<{cls}Read>(`${{base}}/${{row.id}}/revert`,'POST',{{revision:row.revision,target_revision:target}}),draft:row=>({{{draft}}}),export:async()=>{{throw new Error('Export is not enabled for this generated workspace.')}}}}}}\n'''


def frontend_workspace(spec:dict[str,Any])->str:
    visualizations=json.dumps(spec['visualizations'],separators=(',',':'))
    return f"""import {{ useMemo }} from 'react'\nimport type {{ WorkspaceContext }} from '../../platform/workspace/context'\nimport {{ EntityWorkspace }} from '../../platform/workspace/EntityWorkspace'\nimport {{ adapter }} from './adapter'\nexport function Workspace(props:WorkspaceContext){{const value=useMemo(()=>adapter(props.api,props.definition),[props.api,props.definition]);return <EntityWorkspace {{...props}} adapter={{value}} visualizations={{{visualizations}}}/>}}\n"""


def migration_source(spec:dict[str,Any],index:int)->str:
    columns=[];constraints=[]
    for f in spec['fields']:
        columns.append(f"sa.Column({f['key']!r},{_sa_type(f,'sa.')},nullable={f['nullable']})")
        if f['type']=='select':constraints.append(f"sa.CheckConstraint({(f['key']+' IN ('+','.join(sql_string(x) for x in f['choices'])+')')!r},name={('ck_'+spec['key']+'_'+f['key'])!r})")
        if f['required'] and f['type'] in STRING_TYPES:constraints.append(f"sa.CheckConstraint({('length(trim('+f['key']+')) BETWEEN 1 AND '+str(f['max_length']))!r},name={('ck_'+spec['key']+'_'+f['key']+'_required')!r})")
        if f['minimum'] is not None:constraints.append(f"sa.CheckConstraint({(f['key']+' >= '+str(f['minimum']))!r},name={('ck_'+spec['key']+'_'+f['key']+'_minimum')!r})")
        if f['maximum'] is not None:constraints.append(f"sa.CheckConstraint({(f['key']+' <= '+str(f['maximum']))!r},name={('ck_'+spec['key']+'_'+f['key']+'_maximum')!r})")
    all_columns=columns+["sa.Column('revision',sa.Integer(),nullable=False)","sa.Column('archived',sa.Boolean(),nullable=False)","sa.Column('created_by',sa.String(200),nullable=False)","sa.Column('created_at',sa.DateTime(timezone=True),nullable=False)","sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False)"]+constraints+[f"sa.CheckConstraint('revision >= 1',name={('ck_'+spec['key']+'_revision')!r})"]
    indexes=sorted({f['key'] for f in spec['fields'] if f['sortable'] or f['filterable']}|{'archived'})
    return f'''from alembic import op\nimport sqlalchemy as sa\nrevision='tenant_{index:04d}'\ndown_revision='tenant_{index-1:04d}'\nbranch_labels=None\ndepends_on=None\ndef upgrade():\n    op.create_table({spec['key']!r},sa.Column('id',sa.String(36),primary_key=True),{','.join(all_columns)})\n'''+''.join(f"    op.create_index({('ix_'+spec['key']+'_'+field)!r},{spec['key']!r},[{field!r}])\n" for field in indexes)+"def downgrade():raise RuntimeError('Destructive downgrade is disabled. Restore an isolated verified snapshot.')\n"


def generate(root:Path,spec:dict[str,Any],apply:bool=False)->dict[str,Any]:
    root=root.resolve();spec=validate(spec);key=spec['key'];feature=root/'backend/app/features'/key;front=root/'frontend/src/features'/key
    if feature.exists() or front.exists():raise ValueError('Entity feature already exists.')
    manifest_path=root/'backend/app/features/manifest.json';app_path=root/'backend/app/config/application.json';registry_path=root/'frontend/src/app/registry.tsx'
    manifest=json.loads(manifest_path.read_text());app=json.loads(app_path.read_text());registry=registry_path.read_text()
    if key in manifest or any(item['workspace']==key for item in app['navigation']):raise ValueError('Entity is already registered.')
    migrations=sorted((root/'backend/migrations/tenant').glob('[0-9][0-9][0-9][0-9]_*.py'));index=max((int(path.name[:4]) for path in migrations),default=0)+1
    cls=pascal(key.rstrip('s') or key);workspace_import=f"import {{ Workspace as {cls}Workspace }} from '../features/{key}/Workspace'"
    if workspace_import in registry:raise ValueError('Frontend workspace is already registered.')
    files={feature/'__init__.py':'',feature/'models.py':model_source(spec),feature/'schemas.py':schemas_source(spec),feature/'definition.py':definition_source(spec),feature/'service.py':service_source(spec),feature/'entity.py':entity_source(spec),feature/'router.py':router_source(spec),front/'adapter.tsx':frontend_adapter(spec),front/'Workspace.tsx':frontend_workspace(spec),root/'backend/migrations/tenant'/f'{index:04d}_{key}.py':migration_source(spec,index),root/'backend/app/config/entity-specs'/f'{key}.json':json.dumps(spec,indent=2)+'\n'}
    manifest.append(key);app['navigation'].append({'workspace':key,'label':spec['label']})
    registry=registry.replace('export const workspaceRenderers',workspace_import+'\nexport const workspaceRenderers')
    pos=registry.rfind('}\n')
    if pos<0:raise ValueError('Could not update frontend registry.')
    registry=registry[:pos]+f'  {key}: {cls}Workspace,\n'+registry[pos:]
    files[manifest_path]=json.dumps(manifest,indent=2)+'\n';files[app_path]=json.dumps(app,indent=2)+'\n';files[registry_path]=registry
    plan={'entity':key,'migration':f'tenant_{index:04d}','visualizations':spec['visualizations'],'files':[str(path.relative_to(root)) for path in files]}
    if apply:
        for path,content in files.items():atomic(path,content)
    return plan


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('spec',type=Path);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--apply',action='store_true');parser.add_argument('--refresh-adapter',action='store_true');args=parser.parse_args()
    payload=json.loads(args.spec.read_text())
    spec=payload if args.refresh_adapter else validate(payload)
    if args.refresh_adapter:
        target=args.root.resolve()/'frontend/src/features'/spec['key']/'adapter.tsx'
        if not target.is_file():
            print(json.dumps({'skipped':str(target.relative_to(args.root.resolve())),'reason':'custom feature has no generated adapter'},indent=2));return 0
        if args.apply:atomic(target,frontend_adapter(spec))
        print(json.dumps({'refreshed':str(target.relative_to(args.root.resolve()))},indent=2));return 0
    plan=generate(args.root,spec,args.apply);print(json.dumps(plan,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
