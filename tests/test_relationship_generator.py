import importlib.util,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('relationship_generator',ROOT/'scripts/relationship_generator.py')
module=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(module)

def sample():return {'key':'system_work','label':'System work','source_entity':'systems','target_entity':'work_items','forward_label':'Work items','reverse_label':'System','cardinality':'one_to_many','allow_self':False}
def skeleton(tmp_path:Path)->Path:
 root=tmp_path/'app';(root/'backend/app/features').mkdir(parents=True);(root/'backend/app/config').mkdir(parents=True)
 (root/'backend/app/features/manifest.json').write_text('["systems","work_items"]\n')
 (root/'backend/app/config/relationships.json').write_text('[]\n')
 return root

def test_plan_is_non_mutating_and_hashes_result(tmp_path):
 root=skeleton(tmp_path);before=(root/'backend/app/config/relationships.json').read_text();plan=module.generate(root,sample(),False)
 assert (root/'backend/app/config/relationships.json').read_text()==before
 assert plan['relationship']['cardinality']=='one_to_many' and plan['database_migration_required'] is False
 assert plan['before_sha256']!=plan['after_sha256']

def test_apply_registers_definition_atomically_and_rejects_duplicate(tmp_path):
 root=skeleton(tmp_path);module.generate(root,sample(),True)
 payload=json.loads((root/'backend/app/config/relationships.json').read_text())
 assert payload[0]['key']=='system_work' and payload[0]['kind']=='reference' and payload[0]['placement_capacity'] is None
 with pytest.raises(ValueError,match='already exists'):module.generate(root,sample(),True)

def test_validation_rejects_unknown_entities_cardinality_and_keys(tmp_path):
 root=skeleton(tmp_path)
 invalid=[{**sample(),'source_entity':'missing'},{**sample(),'cardinality':'lots'},{**sample(),'unexpected':True},{**sample(),'key':'Bad-Key'}]
 for value in invalid:
  with pytest.raises(ValueError):module.generate(root,value,False)


def test_placement_relationship_requires_capacity(tmp_path):
 root=skeleton(tmp_path)
 placement={**sample(),'key':'system_placement','kind':'placement','placement_capacity':42}
 value=module.generate(root,placement,False)['relationship']
 assert value['kind']=='placement' and value['placement_capacity']==42
 with pytest.raises(ValueError):module.generate(root,{**placement,'placement_capacity':None},False)
 with pytest.raises(ValueError):module.generate(root,{**sample(),'placement_capacity':42},False)
