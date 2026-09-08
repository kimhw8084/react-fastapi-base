import importlib.util
from pathlib import Path
import threading
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lab_server',ROOT/'scripts/lab_server.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
@pytest.fixture
def server():
    server=module.make_server(0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown();server.server_close();thread.join(timeout=5)
def test_compiled_lab_is_served_without_node(server):
    with urlopen(server) as r:
        assert r.status==200
        assert b'react-fastapi-base' in r.read()
        assert r.headers['X-Content-Type-Options']=='nosniff'
        assert "script-src 'self'" in r.headers['Content-Security-Policy']
def test_javascript_content_type_and_source(server):
    with urlopen(server+'/lib/app.js') as r:
        assert r.headers.get_content_type()=='text/javascript'
        assert b'mountLab' in r.read()
def test_external_host_rejected(server):
    with pytest.raises(HTTPError) as e:urlopen(Request(server,headers={'Host':'untrusted.example'}))
    assert e.value.code==403
def test_traversal_and_directory_listing_rejected(server):
    for path in ['/../AGENTS.md','/%2e%2e/AGENTS.md','/.env','/lib/']:
        with pytest.raises(HTTPError) as e:urlopen(server+path)
        assert e.value.code in {403,404}
def test_server_does_not_expose_source_or_database(server):
    for path in ['/backend/app/main.py','/dev','/.local/registry.sqlite3','/src/model.ts']:
        with pytest.raises(HTTPError) as e:urlopen(server+path)
        assert e.value.code in {403,404}
