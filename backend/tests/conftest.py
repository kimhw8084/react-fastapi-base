from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.platform.settings import Settings
from app.platform.database import Database
from app.platform.provision import provision,add_member

@pytest.fixture
def env(tmp_path):
    settings=Settings(environment='test',profile='development',data_root=tmp_path/'data',request_limit_per_minute=1000)
    database=Database(settings)
    tenant=provision(database,'Team A','alice')
    other=provision(database,'Team B','carol')
    add_member(database,tenant,'bob','editor')
    add_member(database,tenant,'victor','viewer')
    clients=[]
    def client(user='alice',**overrides):
        s=settings.model_copy(update={'dev_user':user,**overrides})
        c=TestClient(create_app(s));c.__enter__();clients.append(c)
        b=c.get('/api/v1/bootstrap')
        if b.status_code==200:
            c.headers.update({'X-Tenant-Id':tenant,'X-CSRF-Token':b.json()['csrf_token']})
        return c
    yield {'settings':settings,'db':database,'tenant':tenant,'other':other,'client':client}
    for c in clients:c.__exit__(None,None,None)
    database.close()

@pytest.fixture
def client(env):return env['client']()

@pytest.fixture
def item(client):
    r=client.post('/api/v1/work-items',json={'title':'Investigate backup policy'})
    assert r.status_code==201,r.text
    return r.json()
