import base64
from uuid import uuid4
import pytest

V='/api/v1/workspaces/work_items/views'

def test_personal_views_are_private(env,client):
    row=client.post(V,json={'name':'My work','definition':{'filters':{'status':'open'}}}).json()
    assert row['revision']==1
    bob=env['client']('bob')
    assert bob.get(V).json()==[]
    assert bob.put(V+'/'+row['id'],json={'name':'Steal','revision':1,'definition':{}}).status_code==404

def test_shared_views_readable_but_not_editable_by_others(env,client):
    row=client.post(V,json={'name':'Shared','scope':'team','definition':{}}).json()
    bob=env['client']('bob')
    assert bob.get(V).json()[0]['id']==row['id']
    assert bob.put(V+'/'+row['id'],json={'name':'Changed','scope':'team','revision':1,'definition':{}}).status_code==403

def test_explicit_team_views_require_membership(env,client):
    team=client.post('/api/v1/teams',json={'name':'Architecture','slug':'architecture'});assert team.status_code==201,team.text
    team_id=team.json()['id']
    row=client.post(V,json={'name':'Architecture view','scope':'team','team_id':team_id,'definition':{}});assert row.status_code==201,row.text
    bob=env['client']('bob')
    assert bob.get(V).json()==[]
    added=client.post(f'/api/v1/teams/{team_id}/members',json={'user_id':'bob','role':'member'});assert added.status_code==200,added.text
    assert bob.get(V).json()[0]['team_id']==team_id

def test_viewer_can_save_personal_not_team(env):
    c=env['client']('victor')
    assert c.post(V,json={'name':'Private','definition':{}}).status_code==201
    assert c.post(V,json={'name':'Team','scope':'team','definition':{}}).status_code==403

def test_view_conflicts(client):
    row=client.post(V,json={'name':'First','definition':{}}).json()
    body={'name':'New name','definition':{},'revision':1}
    assert client.put(V+'/'+row['id'],json=body).status_code==200
    assert client.put(V+'/'+row['id'],json=body).status_code==409
    assert client.delete(V+'/'+row['id'],params={'revision':1}).status_code==409
    assert client.delete(V+'/'+row['id'],params={'revision':2}).status_code==204

def test_view_columns_are_sanitized(client):
    row=client.post(V,json={'name':'Columns','definition':{'columns':[{'colId':'title','width':200},{'colId':'invented'},{'colId':'title','width':300}]}}).json()
    assert len(row['definition']['columns'])==1
    assert row['definition']['columns'][0]['width']==200

@pytest.mark.parametrize('definition',[{'filters':{'status':'illegal'}},{'columns':[{'colId':'title','width':100000}]},{'injected':True}])
def test_bad_view_state_rejected(client,definition):
    assert client.post(V,json={'name':'Bad','definition':definition}).status_code==422

def test_upload_download_and_tenant_boundary(env,client,item):
    base=f"/api/v1/work-items/{item['id']}/attachments"
    row=client.post(base,json={'filename':'notes.txt','content_type':'text/plain','content_base64':base64.b64encode(b'Private notes').decode()})
    assert row.status_code==201,row.text
    data=row.json();download=client.get(base+'/'+data['id'])
    assert download.content==b'Private notes'
    assert download.headers['content-type']=='application/octet-stream'
    assert 'attachment' in download.headers['content-disposition']
    assert client.get(base).json()[0]['id']==data['id']
    carol=env['client']('carol');carol.headers['X-Tenant-Id']=env['other']
    assert carol.get(base+'/'+data['id']).status_code==404

@pytest.mark.parametrize('filename,kind,body',[
    ('../secret.txt','text/plain',b'test'),('a\\b.txt','text/plain',b'test'),
    ('a.svg','image/svg+xml',b'<svg/>'),('a.png','image/png',b'not png'),
    ('a.pdf','application/pdf',b'not pdf'),('a.txt','text/plain',b'\xff'),
])
def test_unsafe_upload_rejected(client,item,filename,kind,body):
    r=client.post(f"/api/v1/work-items/{item['id']}/attachments",json={'filename':filename,'content_type':kind,'content_base64':base64.b64encode(body).decode()})
    assert r.status_code==422,r.text


def test_saved_view_persists_supported_visualization(client):
    row=client.post(V,json={'name':'Board view','definition':{'visualization':'board','group_by':'status','filters':{'status':'open'}}})
    assert row.status_code==201,row.text
    data=row.json()['definition']
    assert data['visualization']=='board'
    assert data['group_by']=='status'

def test_saved_view_rejects_unsupported_visualization(client):
    response=client.post(V,json={'name':'Bad projection','definition':{'visualization':'rack'}})
    assert response.status_code==422
    assert response.json()['error']['code']=='invalid_saved_visualization'

def test_record_comments_are_tenant_scoped_and_authorized(env,client,item):
    path=f"/api/v1/records/work_items/{item['id']}/comments"
    created=client.post(path,json={'body':'Check the backup runbook.'})
    assert created.status_code==201,created.text
    assert client.get(path).json()[0]['body']=='Check the backup runbook.'
    bob=env['client']('bob')
    assert bob.get(path).json()[0]['author']=='alice'
    assert bob.delete('/api/v1/records/comments/'+created.json()['id']).status_code==403
    other=env['client']('carol');other.headers['X-Tenant-Id']=env['other'];other.headers['X-CSRF-Token']=other.get('/api/v1/bootstrap').json()['csrf_token']
    assert other.get(path).status_code==404
