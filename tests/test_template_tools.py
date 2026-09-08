from pathlib import Path
import importlib.util
import json
import shutil
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('template_tools',ROOT/'scripts/template_tools.py')
tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)

@pytest.mark.parametrize('theme',['operations','clarity','minimal'])
def test_new_app_has_customization_without_core_edits(tmp_path,theme):
    target=tmp_path/theme
    tools.create_application(ROOT,target,'new-app','New app',theme)
    assert tools.core_manifest(ROOT)==tools.core_manifest(target)
    assert json.loads((target/'backend/app/config/application.json').read_text())['name']=='New app'
    assert json.loads((target/'frontend/public/runtime-config.json').read_text())['defaultTheme']==theme
    assert not (target/'.local').exists()
    assert not (target/'backend/__pycache__').exists()


def test_generator_refuses_overwrite_and_path_id(tmp_path):
    with pytest.raises(ValueError):tools.create_application(ROOT,tmp_path,'valid','Valid')
    with pytest.raises(ValueError):tools.create_application(ROOT,tmp_path/'new','../escape','Valid')


def test_upgrade_is_dry_run_and_conflicts_are_not_overwritten(tmp_path):
    app=tmp_path/'app';incoming=tmp_path/'incoming'
    tools.create_application(ROOT,app,'test-app','Test')
    tools.create_application(ROOT,incoming,'next-app','Next')
    rel='backend/app/platform/errors.py'
    (app/rel).write_text((app/rel).read_text()+'\n# local customization\n')
    (incoming/rel).write_text((incoming/rel).read_text()+'\n# upstream improvement\n')
    before=(app/rel).read_bytes();plan=tools.upgrade_plan(app,incoming)
    assert plan['conflicts']==1
    assert (app/rel).read_bytes()==before
    assert all(row['path'].startswith(tools.MANAGED) for row in plan['changes'])


def test_unmodified_core_is_upgradeable_without_configuration_changes(tmp_path):
    app=tmp_path/'app';incoming=tmp_path/'incoming'
    tools.create_application(ROOT,app,'test-app','Test')
    tools.create_application(ROOT,incoming,'next-app','Next')
    rel='backend/app/platform/errors.py';(incoming/rel).write_text((incoming/rel).read_text()+'\n# new\n')
    plan=tools.upgrade_plan(app,incoming)
    assert plan['conflicts']==0 and plan['changes'][0]['action']=='update'
    assert json.loads((app/'backend/app/config/application.json').read_text())['id']=='test-app'


def test_source_copy_excludes_secrets_private_keys_and_lab_environment(tmp_path):
    files=['.env.production','nested/.env.staging','nested/.env.example','key.pem','private.key','app.sqlite','app.sqlite-wal','.lab-venv/lib/site.py','picture.png','public.js']
    for rel in files:
        p=tmp_path/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture, never a real secret')
    copied={rel for _,rel in tools.source_files(tmp_path)}
    assert copied=={'nested/.env.example','picture.png','public.js'}


def test_generated_application_contains_compiled_lab_without_old_evidence(tmp_path):
    target=tmp_path/'new'
    tools.create_application(ROOT,target,'lab-app','Lab app')
    assert (target/'experience-lab/public/lib/app.js').is_file()
    assert (target/'experience-lab/src/presentation.ts').is_file()
    assert not (target/'checkpoints').exists()
    assert not (target/'evidence').exists()
    lock=json.loads((target/'template.lock.json').read_text())
    assert 'experience-lab/src/presentation.ts' in lock['managed']
    assert 'experience-lab/src/dialog.ts' in lock['managed']
    assert 'experience-lab/src/app.ts' not in lock['managed']

def test_upgrade_apply_and_rollback_are_hash_bound_and_preserve_app_config(tmp_path):
    app=tmp_path/'app';incoming=tmp_path/'incoming'
    tools.create_application(ROOT,app,'test-app','Test')
    tools.create_application(ROOT,incoming,'next-app','Next')
    rel='backend/app/platform/errors.py'
    original=(app/rel).read_bytes();(incoming/rel).write_text((incoming/rel).read_text()+'\n# upstream v2\n')
    config_before=(app/'backend/app/config/application.json').read_bytes()
    plan=tools.upgrade_plan(app,incoming)
    assert plan['conflicts']==0 and plan['plan_hash']
    with pytest.raises(ValueError,match='plan hash'):tools.upgrade_apply(app,incoming,'0'*64,'APP-STOPPED')
    with pytest.raises(ValueError,match='APP-STOPPED'):tools.upgrade_apply(app,incoming,plan['plan_hash'],'')
    journal=tools.upgrade_apply(app,incoming,plan['plan_hash'],'APP-STOPPED')
    assert (app/rel).read_bytes()==(incoming/rel).read_bytes()
    assert (app/'backend/app/config/application.json').read_bytes()==config_before
    data=json.loads(journal.read_text());assert data['status']=='applied'
    tools.upgrade_rollback(app,journal,'APP-STOPPED')
    assert (app/rel).read_bytes()==original
    assert json.loads(journal.read_text())['status']=='rolled_back'


def test_upgrade_rollback_refuses_post_upgrade_edits(tmp_path):
    app=tmp_path/'app';incoming=tmp_path/'incoming'
    tools.create_application(ROOT,app,'test-app','Test')
    tools.create_application(ROOT,incoming,'next-app','Next')
    rel='backend/app/platform/errors.py';(incoming/rel).write_text((incoming/rel).read_text()+'\n# upstream v2\n')
    plan=tools.upgrade_plan(app,incoming);journal=tools.upgrade_apply(app,incoming,plan['plan_hash'],'APP-STOPPED')
    (app/rel).write_text((app/rel).read_text()+'\n# human post-upgrade edit\n')
    with pytest.raises(ValueError,match='rollback refused'):tools.upgrade_rollback(app,journal,'APP-STOPPED')
