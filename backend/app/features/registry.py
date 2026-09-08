"""App-owned feature composition. Modules are local code, never browser inputs."""
import importlib
import json
from pathlib import Path
import re

names=json.loads(Path(__file__).with_name('manifest.json').read_text())
if not isinstance(names,list) or len(names)!=len(set(names)) or not names:
    raise ValueError('Feature manifest must contain distinct local feature names.')
DEFINITIONS={}
ENTITY_BINDINGS={}
ROUTERS=[]
for name in names:
    if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,39}',name):
        raise ValueError('Invalid local feature module name.')
    DEFINITIONS[name]=importlib.import_module(f'app.features.{name}.definition').definition
    ROUTERS.append(importlib.import_module(f'app.features.{name}.router').router)
    try:
        ENTITY_BINDINGS[name]=importlib.import_module(f'app.features.{name}.entity').binding()
    except ModuleNotFoundError as error:
        if error.name != f'app.features.{name}.entity':
            raise
