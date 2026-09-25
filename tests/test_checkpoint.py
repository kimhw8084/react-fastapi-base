import json
from pathlib import Path
import subprocess
import sys
import zipfile
from scripts import generate_checkpoint_manifest

ROOT=Path(__file__).resolve().parents[1]

def test_checkpoint_has_single_generated_manifest_and_no_secrets(tmp_path):
    # The script owns its target under checkpoints; use a unique deterministic-safe label.
    label='pytest-checkpoint'
    result=subprocess.run([sys.executable,'scripts/checkpoint.py',label],cwd=ROOT,text=True,capture_output=True,check=True)
    payload=json.loads(result.stdout)
    archive=Path(payload['archive'])
    try:
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            assert names.count('react-fastapi-base/CHECKPOINT_MANIFEST.json')==1
            assert not any('/.git/' in name or '/node_modules/' in name or name.endswith(('.sqlite3','.pem','.key')) for name in names)
            manifest=json.loads(z.read('react-fastapi-base/CHECKPOINT_MANIFEST.json'))
            assert 'CHECKPOINT_MANIFEST.json' not in manifest
    finally:
        archive.unlink(missing_ok=True)
        archive.with_suffix('.zip.sha256').unlink(missing_ok=True)

def test_repository_checkpoint_check_rejects_stale_manifest(tmp_path, monkeypatch, capsys):
    (tmp_path/'source.txt').write_text('current source\n', encoding='utf-8')
    manifest=tmp_path/'CHECKPOINT_MANIFEST.json'
    manifest.write_text('{"files": {}}\n', encoding='utf-8')
    monkeypatch.setattr(generate_checkpoint_manifest, 'ROOT', tmp_path)
    monkeypatch.setattr(generate_checkpoint_manifest, 'MANIFEST', manifest)
    monkeypatch.setattr(sys, 'argv', ['generate_checkpoint_manifest.py', '--check'])

    assert generate_checkpoint_manifest.main() == 1
    assert 'Checkpoint manifest is stale' in capsys.readouterr().out
