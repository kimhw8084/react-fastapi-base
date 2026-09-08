#!/usr/bin/env python3
"""Deterministic application generation and conservative, three-way core upgrades.
Never invokes an AI tool, modifies the source template, or overwrites app config.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import os
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
PLATFORM_VERSION=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
MANAGED=('backend/app/platform/','frontend/src/platform/','experience-lab/src/base.ts','experience-lab/src/dialog.ts','experience-lab/src/icons.ts','experience-lab/src/presentation.ts','experience-lab/src/model.ts','experience-lab/src/validation.ts','experience-lab/src/table.ts','experience-lab/src/scheduling.ts','experience-lab/src/spatial.ts','experience-lab/src/charts.ts','experience-lab/src/editors.ts','experience-lab/src/windows.ts','experience-lab/src/manufacturing','experience-lab/src/composition.ts')
EXCLUDED={'.git','.local','.evidence','.template-upgrades','.venv','.lab-venv','venv','node_modules','dist','__pycache__','.pytest_cache','test-results','playwright-report','.generated-smoke','verification','checkpoints','evidence'}

def digest(path: Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def source_files(root: Path):
    for path in sorted(root.rglob('*')):
        rel=path.relative_to(root)
        if not path.is_file() or path.is_symlink() or set(rel.parts)&EXCLUDED:continue
        if path.name.startswith('.env') and not any(x in path.name for x in ('example','sample','template')):continue
        if path.name=='.coverage' or path.name.endswith(('-wal','-shm','-journal','.pid')):continue
        if path.suffix.lower() in {'.pyc','.db','.sqlite','.sqlite3','.zip','.pem','.key','.ttf','.otf','.woff','.woff2'}:continue
        yield path,rel.as_posix()

def core_manifest(root: Path)->dict:
    return {rel:digest(path) for path,rel in source_files(root) if rel.startswith(MANAGED)}

def create_application(source: Path, target: Path, app_id: str, name: str, theme: str='operations'):
    source=source.resolve();target=target.absolute()
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,39}',app_id):raise ValueError('Application ID must be a lowercase slug.')
    if not 1<=len(name)<=80 or any(ord(c)<32 for c in name):raise ValueError('Name must be 1–80 printable characters.')
    if theme not in {'operations','clarity','minimal'}:raise ValueError('Unknown theme.')
    if target.exists() or target.is_symlink():raise ValueError('Destination must not exist.')
    if source==target or source in target.parents:raise ValueError('Create applications outside the template source.')
    target.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.react-fastapi-create-',dir=target.parent))
    try:
        for path,rel in source_files(source):
            output=stage/rel;output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,output)
        config_path=stage/'backend/app/config/application.json'
        config=json.loads(config_path.read_text());config.update(id=app_id,name=name,theme=theme)
        config_path.write_text(json.dumps(config,indent=2)+'\n')
        runtime_path=stage/'frontend/public/runtime-config.json'
        runtime=json.loads(runtime_path.read_text());runtime.update(defaultTheme=theme,titleOverride=name)
        runtime_path.write_text(json.dumps(runtime,indent=2)+'\n')
        (stage/'template.lock.json').write_text(json.dumps({'schema_version':1,'platform_version':PLATFORM_VERSION,'reference_source_commit':'66244b997a70b85e6e887870c96db958f3f0d22d','managed':core_manifest(stage)},indent=2)+'\n')
        if target.exists():raise ValueError('Destination appeared while generating.')
        os.rename(stage,target)
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True);raise
    return target

def _canonical(value)->bytes:return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def _plan_hash(changes:list[dict])->str:return hashlib.sha256(_canonical(changes)).hexdigest()
def _safe_managed_path(root:Path,rel:str)->Path:
    if not rel.startswith(MANAGED) or '..' in Path(rel).parts:raise ValueError('Invalid managed file path.')
    path=root/rel
    if path.is_symlink():raise ValueError('A managed file must not be a symbolic link.')
    return path
def _atomic_bytes(path:Path,payload:bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.upgrade-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as handle:
            handle.write(payload);handle.flush();os.fsync(handle.fileno())
        os.replace(name,path)
        try:
            directory=os.open(path.parent,os.O_RDONLY);os.fsync(directory);os.close(directory)
        except OSError:pass
    finally:
        try:os.unlink(name)
        except FileNotFoundError:pass

def _upgrade_root(app:Path)->Path:
    path=app/'.template-upgrades'
    if path.is_symlink():raise ValueError('Upgrade journal directory must not be a symbolic link.')
    path.mkdir(exist_ok=True)
    return path

def upgrade_plan(app: Path,incoming: Path)->dict:
    app=app.resolve();incoming=incoming.resolve()
    baseline=json.loads((app/'template.lock.json').read_text())
    if baseline.get('schema_version')!=1:raise ValueError('Unsupported template lock.')
    previous=baseline['managed'];new=core_manifest(incoming);changes=[]
    for rel in sorted(set(previous)|set(new)):
        current_path=_safe_managed_path(app,rel)
        current=digest(current_path) if current_path.is_file() else None
        old=previous.get(rel);next_hash=new.get(rel)
        if current==next_hash:kind='unchanged'
        elif current==old:kind='update' if next_hash is not None else 'remove'
        elif old==next_hash:kind='preserve_local'
        else:kind='conflict'
        if kind!='unchanged':changes.append({'path':rel,'action':kind,'base':old,'current':current,'incoming':next_hash})
    return {'schema_version':1,'mode':'dry_run','conflicts':sum(c['action']=='conflict' for c in changes),'plan_hash':_plan_hash(changes),'changes':changes,
            'note':'Application config and feature directories are outside managed ownership. Apply requires APP-STOPPED acknowledgement and an exact plan hash.'}

def upgrade_apply(app:Path,incoming:Path,expected_plan_hash:str,maintenance:str)->Path:
    app=app.resolve();incoming=incoming.resolve()
    if maintenance!='APP-STOPPED':raise ValueError('Upgrade apply requires --maintenance APP-STOPPED.')
    plan=upgrade_plan(app,incoming)
    if plan['conflicts']:raise ValueError('Upgrade has conflicts; resolve them before apply.')
    if not expected_plan_hash or expected_plan_hash!=plan['plan_hash']:raise ValueError('Upgrade plan hash changed; generate and review a fresh plan.')
    actionable=[row for row in plan['changes'] if row['action'] in {'update','remove'}]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+plan['plan_hash'][:12]
    journal_dir=_upgrade_root(app)/stamp
    if journal_dir.exists():raise ValueError('Upgrade journal already exists.')
    backup=journal_dir/'before';backup.mkdir(parents=True)
    lock_path=app/'template.lock.json'
    lock_before=lock_path.read_bytes();_atomic_bytes(backup/'template.lock.json',lock_before)
    journal={'schema_version':1,'status':'applying','created_at':datetime.now(timezone.utc).isoformat(),'plan_hash':plan['plan_hash'],'changes':[]}
    _atomic_bytes(journal_dir/'journal.json',json.dumps(journal,indent=2).encode()+b'\n')
    try:
        for row in actionable:
            rel=row['path'];current_path=_safe_managed_path(app,rel);current=digest(current_path) if current_path.is_file() else None
            if current!=row['current']:raise ValueError(f'Managed file changed after planning: {rel}')
            backup_path=backup/rel
            if current_path.is_file():_atomic_bytes(backup_path,current_path.read_bytes())
            incoming_path=_safe_managed_path(incoming,rel)
            if row['action']=='update':
                if not incoming_path.is_file() or digest(incoming_path)!=row['incoming']:raise ValueError(f'Incoming managed file drifted: {rel}')
                _atomic_bytes(current_path,incoming_path.read_bytes())
            else:
                if current_path.exists():current_path.unlink()
            journal['changes'].append({'path':rel,'action':row['action'],'before':row['current'],'after':row['incoming'],'had_before':current is not None})
            _atomic_bytes(journal_dir/'journal.json',json.dumps(journal,indent=2).encode()+b'\n')
        incoming_lock=incoming/'template.lock.json'
        incoming_version=json.loads(incoming_lock.read_text()).get('platform_version') if incoming_lock.is_file() else 'incoming'
        lock=json.loads(lock_before);lock['platform_version']=incoming_version;lock['managed']=core_manifest(incoming)
        _atomic_bytes(lock_path,json.dumps(lock,indent=2).encode()+b'\n')
        journal['status']='applied';journal['applied_at']=datetime.now(timezone.utc).isoformat();journal['template_lock_after']=digest(lock_path)
        _atomic_bytes(journal_dir/'journal.json',json.dumps(journal,indent=2).encode()+b'\n')
        return journal_dir/'journal.json'
    except BaseException:
        # A partial apply is intentionally left journaled; rollback performs validation/restoration.
        journal['status']='partial';journal['failed_at']=datetime.now(timezone.utc).isoformat()
        _atomic_bytes(journal_dir/'journal.json',json.dumps(journal,indent=2).encode()+b'\n')
        raise

def upgrade_rollback(app:Path,journal_path:Path,maintenance:str)->None:
    app=app.resolve();journal_path=journal_path.resolve()
    if maintenance!='APP-STOPPED':raise ValueError('Rollback requires --maintenance APP-STOPPED.')
    root=_upgrade_root(app).resolve()
    if root not in journal_path.parents or journal_path.name!='journal.json':raise ValueError('Journal must belong to this application.')
    journal=json.loads(journal_path.read_text())
    if journal.get('schema_version')!=1 or journal.get('status') not in {'applied','partial'}:raise ValueError('Journal is not rollbackable.')
    backup=journal_path.parent/'before'
    # Refuse to erase post-upgrade human edits.
    for row in journal.get('changes',[]):
        path=_safe_managed_path(app,row['path']);current=digest(path) if path.is_file() else None
        if current!=row['after']:raise ValueError(f'Managed file changed after upgrade; rollback refused: {row["path"]}')
    for row in reversed(journal.get('changes',[])):
        path=_safe_managed_path(app,row['path']);before=backup/row['path']
        if row['had_before']:
            if not before.is_file() or digest(before)!=row['before']:raise ValueError(f'Upgrade backup is invalid: {row["path"]}')
            _atomic_bytes(path,before.read_bytes())
        elif path.exists():path.unlink()
    lock_backup=backup/'template.lock.json'
    if not lock_backup.is_file():raise ValueError('Template lock backup is missing.')
    _atomic_bytes(app/'template.lock.json',lock_backup.read_bytes())
    journal['status']='rolled_back';journal['rolled_back_at']=datetime.now(timezone.utc).isoformat()
    _atomic_bytes(journal_path,json.dumps(journal,indent=2).encode()+b'\n')

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('create');c.add_argument('target',type=Path);c.add_argument('--id',required=True);c.add_argument('--name',required=True);c.add_argument('--theme',default='operations')
    u=sub.add_parser('upgrade-plan');u.add_argument('--app',type=Path,required=True);u.add_argument('--incoming',type=Path,required=True)
    u=sub.add_parser('upgrade-apply');u.add_argument('--app',type=Path,required=True);u.add_argument('--incoming',type=Path,required=True);u.add_argument('--plan-hash',required=True);u.add_argument('--maintenance',required=True)
    u=sub.add_parser('upgrade-rollback');u.add_argument('--app',type=Path,required=True);u.add_argument('--journal',type=Path,required=True);u.add_argument('--maintenance',required=True)
    a=p.parse_args()
    if a.command=='create':print(create_application(ROOT,a.target,a.id,a.name,a.theme));return 0
    if a.command=='upgrade-plan':
        plan=upgrade_plan(a.app,a.incoming);print(json.dumps(plan,indent=2));return 1 if plan['conflicts'] else 0
    if a.command=='upgrade-apply':print(upgrade_apply(a.app,a.incoming,a.plan_hash,a.maintenance));return 0
    if a.command=='upgrade-rollback':upgrade_rollback(a.app,a.journal,a.maintenance);print('Rollback completed.');return 0
    return 1
if __name__=='__main__':raise SystemExit(main())
