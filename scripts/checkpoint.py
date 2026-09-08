#!/usr/bin/env python3
"""Create an atomic, verifiable source checkpoint without dependencies or secrets."""
from pathlib import Path
import argparse,hashlib,json,os,zipfile
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'node_modules','.git','.venv','.lab-venv','venv','__pycache__','.pytest_cache','.local','.evidence','checkpoints','dist','coverage','test-results','playwright-report','.cache'}
def source_files():
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file() or p.is_symlink():continue
  rel=p.relative_to(ROOT)
  if any(s in EXCLUDE for s in rel.parts):continue
  if rel.as_posix()=='CHECKPOINT_MANIFEST.json':continue
  if p.suffix.lower() in {'.db','.sqlite','.sqlite3','.pyc','.pem','.key','.ttf','.otf','.woff','.woff2'}:continue
  if p.name.endswith(('-wal','-shm','-journal','.pid')):continue
  if p.name.startswith('.env') and not any(s in p.name for s in ['example','sample','template']):continue
  yield p,rel.as_posix()
def checkpoint(label):
 if not label.replace('-','').replace('.','').isalnum():raise ValueError('Invalid label')
 folder=ROOT/'checkpoints';folder.mkdir(exist_ok=True)
 target=folder/f'react-fastapi-base-{label}.zip';tmp=target.with_suffix('.tmp')
 files=list(source_files())
 manifest={rel:hashlib.sha256(p.read_bytes()).hexdigest() for p,rel in files}
 with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
  for p,rel in files:z.write(p,'react-fastapi-base/'+rel)
  z.writestr('react-fastapi-base/CHECKPOINT_MANIFEST.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(tmp) as z:
  assert z.testzip() is None
  for rel,h in manifest.items():assert hashlib.sha256(z.read('react-fastapi-base/'+rel)).hexdigest()==h
 os.replace(tmp,target)
 digest=hashlib.sha256(target.read_bytes()).hexdigest()
 target.with_suffix('.zip.sha256').write_text(f'{digest}  {target.name}\n')
 print(json.dumps({'archive':str(target),'files':len(files),'sha256':digest}))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('label',nargs='?',default='checkpoint')
 checkpoint(parser.parse_args().label)
