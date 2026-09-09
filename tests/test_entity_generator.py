import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('entity_generator',ROOT/'scripts/entity_generator.py')
module=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(module)

def sample():
    return {'key':'systems','label':'Systems','singular':'system','description':'Generated test entity','primary_field':'name','visualizations':['table','board'],'fields':[{'key':'name','label':'Name','type':'text','required':True,'max_length':120,'searchable':True},{'key':'status','label':'Status','type':'select','choices':['active','retired'],'default':'active','filterable':True}]}

def typed_sample():
    return {
      'key':'systems','label':'Systems','singular':'system','description':'Generated typed entity',
      'primary_field':'name','visualizations':['table','board'],
      'fields':[
        {'key':'name','label':'Name','type':'text','required':True,'max_length':120,'searchable':True},
        {'key':'notes','label':'Notes','type':'textarea','max_length':2000},
        {'key':'status','label':'Status','type':'select','choices':['planned','active','retired'],'default':'planned','filterable':True},
        {'key':'capacity','label':'Capacity','type':'integer','minimum':0,'maximum':1000,'step':1,'filterable':True},
        {'key':'load_factor','label':'Load factor','type':'number','minimum':0,'maximum':1,'step':0.01,'default':0.25},
        {'key':'critical','label':'Critical','type':'boolean','default':False,'filterable':True},
        {'key':'commissioned_on','label':'Commissioned on','type':'date'},
        {'key':'review_at','label':'Review at','type':'datetime'},
        {'key':'owner_email','label':'Owner email','type':'email','max_length':254,'searchable':True},
        {'key':'runbook_url','label':'Runbook URL','type':'url','max_length':2048,'searchable':True},
      ],
    }

def skeleton(tmp_path:Path)->Path:
    root=tmp_path/'app'
    (root/'backend/app/features').mkdir(parents=True);(root/'backend/app/config').mkdir(parents=True);(root/'backend/migrations/tenant').mkdir(parents=True);(root/'frontend/src/app').mkdir(parents=True)
    (root/'backend/app/features/manifest.json').write_text('["work_items"]\n')
    (root/'backend/app/config/application.json').write_text(json.dumps({'navigation':[{'workspace':'work_items','label':'Work items'}]}))
    (root/'frontend/src/app/registry.tsx').write_text("import { Workspace as WorkItemsWorkspace } from '../features/work-items/Workspace'\nexport const workspaceRenderers = {\n  work_items: WorkItemsWorkspace,\n}\n")
    (root/'backend/migrations/tenant/0001_tenant.py').write_text("revision='tenant_0001'\ndown_revision=None\n")
    return root

def test_generator_plan_is_non_mutating(tmp_path):
    root=skeleton(tmp_path);before=(root/'backend/app/features/manifest.json').read_text()
    plan=module.generate(root,sample(),False)
    assert plan['migration']=='tenant_0002'
    assert (root/'backend/app/features/manifest.json').read_text()==before
    assert not (root/'backend/app/features/systems').exists()

def test_generator_apply_produces_compilable_backend_and_registry(tmp_path):
    root=skeleton(tmp_path);plan=module.generate(root,sample(),True)
    for relative in plan['files']:
        path=root/relative
        assert path.is_file()
        if path.suffix=='.py':compile(path.read_text(),str(path),'exec')
    router=(root/'backend/app/features/systems/router.py').read_text()
    assert 'response_model=list[SystemRead]' in router
    manifest=json.loads((root/'backend/app/features/manifest.json').read_text())
    assert manifest==['work_items','systems']
    registry=(root/'frontend/src/app/registry.tsx').read_text()
    assert "Workspace as SystemWorkspace" in registry and 'systems: SystemWorkspace' in registry
    workspace=(root/'frontend/src/features/systems/Workspace.tsx').read_text()
    assert 'EntityWorkspace' in workspace and 'visualizations={[\"table\",\"board\"]}' in workspace
    definition=(root/'backend/app/features/systems/definition.py').read_text()
    assert "'board'" in definition
    with pytest.raises(ValueError,match='already exists'):module.generate(root,sample(),True)

def test_generator_rejects_unsafe_or_ambiguous_specs():
    invalid=[
      {**sample(),'key':'Bad-Key'},
      {**sample(),'unexpected':True},
      {**sample(),'fields':[{'key':'revision','label':'Revision','type':'text'}]},
      {**sample(),'fields':[{'key':'metadata','label':'Metadata','type':'json'}]},
      {**sample(),'fields':[{'key':'status','label':'Status','type':'select','choices':[]}]},
      {**sample(),'primary_field':'missing'},
      {**sample(),'visualizations':['table','table']},
      {**sample(),'visualizations':['wafer']},
    ]
    for value in invalid:
        with pytest.raises(ValueError):module.validate(value)

def test_typed_fields_normalize_nullable_defaults_and_bounds():
    value=module.validate(typed_sample())
    by_key={field['key']:field for field in value['fields']}
    assert by_key['capacity']['nullable'] is True
    assert by_key['load_factor']['nullable'] is False
    assert by_key['load_factor']['default']==0.25
    assert by_key['critical']['nullable'] is False
    assert by_key['critical']['default'] is False
    assert by_key['commissioned_on']['nullable'] is True
    assert by_key['review_at']['nullable'] is True
    assert by_key['owner_email']['max_length']==254
    assert by_key['runbook_url']['max_length']==2048

def test_typed_field_validation_rejects_incompatible_configuration():
    bad=[]
    required_default=typed_sample();required_default['fields'][0]['default']='x';bad.append(required_default)
    numeric_search=typed_sample();numeric_search['fields'][3]['searchable']=True;bad.append(numeric_search)
    text_filter=typed_sample();text_filter['fields'][1]['filterable']=True;bad.append(text_filter)
    reversed_bounds=typed_sample();reversed_bounds['fields'][3]['minimum']=5;reversed_bounds['fields'][3]['maximum']=1;bad.append(reversed_bounds)
    invalid_step=typed_sample();invalid_step['fields'][4]['step']=0;bad.append(invalid_step)
    invalid_number_default=typed_sample();invalid_number_default['fields'][4]['default']=2;bad.append(invalid_number_default)
    naive_datetime=typed_sample();naive_datetime['fields'][7]['default']='2026-09-07T10:00:00';bad.append(naive_datetime)
    boolean_choices=typed_sample();boolean_choices['fields'][5]['choices']=['true'];bad.append(boolean_choices)
    for value in bad:
        with pytest.raises(ValueError):module.validate(value)

def test_typed_generator_emits_typed_backend_frontend_and_constraints(tmp_path):
    root=skeleton(tmp_path);plan=module.generate(root,typed_sample(),True)
    assert plan['visualizations']==['table','board']
    model=(root/'backend/app/features/systems/models.py').read_text()
    schemas=(root/'backend/app/features/systems/schemas.py').read_text()
    service=(root/'backend/app/features/systems/service.py').read_text()
    router=(root/'backend/app/features/systems/router.py').read_text()
    definition=(root/'backend/app/features/systems/definition.py').read_text()
    migration=(root/'backend/migrations/tenant/0002_systems.py').read_text()
    adapter=(root/'frontend/src/features/systems/adapter.tsx').read_text()
    assert 'capacity: Mapped[int | None]' in model
    assert 'load_factor: Mapped[float]' in model and 'default=0.25' in model
    assert 'critical: Mapped[bool]' in model and 'default=False' in model
    assert 'commissioned_on: Mapped[date | None]' in model
    assert 'review_at: Mapped[datetime | None]' in model
    assert 'capacity: int | None=Field(default=None,ge=0,le=1000)' in schemas
    assert 'load_factor: float=Field(default=0.25,ge=0,le=1)' in schemas
    assert "'critical':(System.critical,('true','false'),lambda value:value=='true','boolean')" in service
    assert "'capacity':(System.capacity,(),int,'numeric')" in service
    assert 'decode_query_list(sorts' in router and 'advanced_filters' in router
    assert "kind='datetime'" in definition and "nullable=True" in definition
    assert "CheckConstraint('capacity >= 0'" in migration
    assert "CheckConstraint('load_factor <= 1'" in migration
    assert 'parseIntegerDraft' in adapter and 'parseNumberDraft' in adapter
    assert 'parseBooleanDraft' in adapter and 'datetimeInputToIso' in adapter


def test_advanced_visualizations_are_supported():
    value=module.validate({**sample(),'visualizations':['table','timeline','calendar','gantt','dashboard','graph','rack']})
    assert value['visualizations']==['table','timeline','calendar','gantt','dashboard','graph','rack']

def rich_sample():
    return {
      'key':'knowledge_items','label':'Knowledge items','singular':'knowledge item','description':'Rich generated entity',
      'primary_field':'name','visualizations':['table','timeline','dashboard','graph'],
      'fields':[
        {'key':'name','label':'Name','type':'text','required':True,'max_length':120,'searchable':True},
        {'key':'body','label':'Body','type':'markdown','max_length':50000,'searchable':True},
        {'key':'procedure','label':'Procedure','type':'code','max_length':100000},
        {'key':'properties','label':'Properties','type':'json','max_length':12000,'default':{'owner':'ops'}},
        {'key':'tags','label':'Tags','type':'multiselect','choices':['runbook','recovery','standard'],'default':['runbook']},
        {'key':'utilization','label':'Utilization','type':'percent','default':50,'step':0.1},
        {'key':'retention','label':'Retention','type':'duration','unit':'h','default':24,'step':0.5},
        {'key':'threshold','label':'Threshold','type':'scientific','default':0.0001},
        {'key':'temperature','label':'Temperature','type':'unit_number','unit':'°C','default':25.0,'step':0.1},
        {'key':'long_description','label':'Long description','type':'long_text','max_length':3000},
        {'key':'ratio','label':'Ratio','type':'decimal','precision':4,'display_format':'0.0000'},
        {'key':'range_limit','label':'Range limit','type':'range','minimum':0,'maximum':100},
        {'key':'tolerance','label':'Tolerance','type':'tolerance','minimum':0,'maximum':10},
        {'key':'attributes','label':'Attributes','type':'object','max_length':12000},
        {'key':'points','label':'Points','type':'array','max_length':12000},
        {'key':'modes','label':'Modes','type':'multi_enum','choices':['auto','manual']},
        {'key':'coordinates','label':'Coordinates','type':'coordinates','max_length':4000},
        {'key':'attachment','label':'Attachment','type':'file','max_length':500},
        {'key':'image','label':'Image','type':'image','max_length':500},
        {'key':'linked_record','label':'Linked record','type':'relationship','max_length':64},
        {'key':'calculated_formula','label':'Calculated formula','type':'formula'},
        {'key':'server_score','label':'Server score','type':'computed','read_only':True},
      ],
    }


def test_rich_field_types_normalize_semantics_and_reject_unsafe_specs():
    value=module.validate(rich_sample());by_key={field['key']:field for field in value['fields']}
    assert by_key['properties']['column'] is False
    assert by_key['tags']['column'] is False and by_key['tags']['sortable'] is False
    assert by_key['utilization']['minimum']==0 and by_key['utilization']['maximum']==100 and by_key['utilization']['unit']=='%'
    assert by_key['retention']['minimum']==0 and by_key['retention']['unit']=='h'
    assert by_key['temperature']['unit']=='°C'
    invalid=[]
    wrong_json=rich_sample();wrong_json['fields'][3]['default']=[];invalid.append(wrong_json)
    bad_tags=rich_sample();bad_tags['fields'][4]['default']=['unknown'];invalid.append(bad_tags)
    duplicate_tags=rich_sample();duplicate_tags['fields'][4]['default']=['runbook','runbook'];invalid.append(duplicate_tags)
    bad_percent=rich_sample();bad_percent['fields'][5]['default']=101;invalid.append(bad_percent)
    negative_duration=rich_sample();negative_duration['fields'][6]['default']=-1;invalid.append(negative_duration)
    missing_unit=rich_sample();missing_unit['fields'][8].pop('unit');invalid.append(missing_unit)
    text_unit=rich_sample();text_unit['fields'][0]['unit']='kg';invalid.append(text_unit)
    for spec in invalid:
        with pytest.raises(ValueError):module.validate(spec)


def test_rich_generator_emits_json_multiselect_units_and_safe_frontend(tmp_path):
    root=skeleton(tmp_path);plan=module.generate(root,rich_sample(),True)
    for relative in plan['files']:
        path=root/relative
        if path.suffix=='.py':compile(path.read_text(),str(path),'exec')
    model=(root/'backend/app/features/knowledge_items/models.py').read_text()
    schemas=(root/'backend/app/features/knowledge_items/schemas.py').read_text()
    definition=(root/'backend/app/features/knowledge_items/definition.py').read_text()
    migration=(root/'backend/migrations/tenant/0002_knowledge_items.py').read_text()
    adapter=(root/'frontend/src/features/knowledge_items/adapter.tsx').read_text()
    assert 'from typing import Any' in model and 'JSON' in model
    assert 'properties: Mapped[dict[str,Any]]' in model and 'tags: Mapped[list[str]]' in model
    assert "tags: list[Literal['runbook','recovery','standard']]=Field(default=['runbook'],max_length=100)" in schemas
    assert 'validate_properties_size' in schemas and '12000' in schemas
    assert "kind='unit_number'" in definition and "unit='°C'" in definition
    assert "sa.Column('properties',sa.JSON" in migration and "sa.Column('tags',sa.JSON" in migration
    assert 'parseJsonObjectDraft' in adapter and 'parseMultiSelectDraft' in adapter
    assert 'readJsonDraft' in adapter and 'readMultiSelectDraft' in adapter
    assert 'parseNumberDraft' in adapter
    assert 'parseJsonArrayDraft' in adapter and 'readJsonArrayDraft' in adapter
    assert 'calculated_formula' not in schemas.split('class KnowledgeItemRead',1)[0]
    assert 'server_score: Any | None=Field(default=None)' in schemas
    assert "precision=4" in definition and "display_format='0.0000'" in definition
    assert "computed=True" in definition and "read_only=True" in definition
