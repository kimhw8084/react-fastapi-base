from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

LOCK_TEST = """
import sqlite3,sys
c=sqlite3.connect(sys.argv[1],timeout=0.15)
try:
 c.execute('BEGIN IMMEDIATE');c.rollback();sys.exit(9)
except sqlite3.OperationalError as e:
 sys.exit(0 if 'locked' in str(e).lower() else 8)
"""
CRASH_TEST = """
import os,sqlite3,sys
c=sqlite3.connect(sys.argv[1])
c.execute('BEGIN IMMEDIATE');c.execute('INSERT INTO sample VALUES (99)');os._exit(0)
"""

def probe(parent: Path) -> dict:
    """Destructive tests are confined to a newly created scratch subdirectory.

    PASS is diagnostic only: no short test proves cross-host locking, power-loss
    durability, or a vendor's unsupported filesystem semantics.
    """
    if not parent.is_dir() or parent.is_symlink():raise ValueError('Provide an existing non-symlink scratch parent, not a live database path.')
    root=Path(tempfile.mkdtemp(prefix='golden-probe-',dir=parent))
    checks={}
    try:
        raw=root/'sample';raw.write_bytes(b'test')
        with raw.open('rb') as file:os.fsync(file.fileno())
        raw.rename(root/'renamed');checks['create_fsync_rename']=(root/'renamed').read_bytes()==b'test'
        path=root/'probe.sqlite3'
        connection=sqlite3.connect(path)
        try:
            connection.execute('PRAGMA journal_mode=DELETE');connection.execute('CREATE TABLE sample(value INTEGER)');connection.commit()
            connection.execute('BEGIN IMMEDIATE')
            child=subprocess.run([sys.executable,'-c',LOCK_TEST,str(path)],capture_output=True,timeout=5)
            checks['same_host_writer_exclusion']=child.returncode==0
            connection.rollback()
        finally:
            connection.close()
        child=subprocess.run([sys.executable,'-c',CRASH_TEST,str(path)],capture_output=True,timeout=5)
        connection=sqlite3.connect(path)
        try:
            checks['process_exit_rollback']=child.returncode==0 and connection.execute('SELECT COUNT(*) FROM sample').fetchone()[0]==0
            checks['integrity_check']=connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        finally:
            connection.close()
        return {'schema_version':1,'checks':checks,'diagnostic_pass':all(checks.values()),'production_approved':False,
                'limitations':['No cross-host test','No power-loss test','No provider compatibility guarantee','No permission or identity qualification'],
                'required_next_evidence':'Provider-supported SQLite semantics and deployment-specific company qualification.'}
    finally:shutil.rmtree(root,ignore_errors=True)
