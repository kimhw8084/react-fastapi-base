from uuid import uuid4
import base64
import pytest
from app.features.work_items.exchange import export_csv,export_json,export_xlsx,preview_csv,preview_json,preview_xlsx,safe_cell
from app.features.work_items.schemas import WorkItemCreate
from app.platform.errors import AppError

@pytest.mark.parametrize('value',['=SUM(1,2)','+cmd','-42','@danger',"'leading",'plain','회사','  =SUM(A1)','line\nbreak'])
def test_csv_roundtrip_and_formula_safety(value):
    row=WorkItemCreate(title='Title',description=value)
    text=export_csv([row]);preview=preview_csv(text)
    assert preview.errors==[]
    assert preview.rows[0].description==value
    if value.lstrip().startswith(('=','+','-','@')):assert safe_cell(value).startswith("'")

def test_xlsx_roundtrip_and_api_commit(client):
    row=WorkItemCreate(title='Spreadsheet item',description='=not-a-formula')
    content=export_xlsx([row]);preview=preview_xlsx(content)
    assert preview.errors==[] and preview.rows[0].description=='=not-a-formula'
    encoded=base64.b64encode(content).decode()
    checked=client.post('/api/v1/work-items/import/preview',json={'xlsx_base64':encoded})
    assert checked.status_code==200 and checked.json()['rows'][0]['title']=='Spreadsheet item'
    committed=client.post('/api/v1/work-items/import/commit',json={'xlsx_base64':encoded,'fingerprint':checked.json()['fingerprint']},headers={'Idempotency-Key':str(uuid4())})
    assert committed.status_code==200 and committed.json()[0]['title']=='Spreadsheet item'

def test_json_snapshot_roundtrip_and_api_export(client):
    row=WorkItemCreate(title='Snapshot item',description='safe',status='open',priority='high')
    content=export_json([row]);preview=preview_json(content)
    assert preview.errors==[] and preview.rows[0].title=='Snapshot item'
    checked=client.post('/api/v1/work-items/import/preview',json={'json_snapshot':content})
    assert checked.status_code==200 and checked.json()['rows'][0]['title']=='Snapshot item'
    exported=client.get('/api/v1/work-items/export.json')
    assert exported.status_code==200 and exported.headers['content-type'].startswith('application/json')

def test_preview_invalid_row(client):
    result=client.post('/api/v1/work-items/import/preview',json={'csv':'title,description,status,priority\nBad,,wrong,high\n'})
    assert result.status_code==200 and result.json()['errors']
    assert client.get('/api/v1/work-items').json()['total']==0

def test_import_review_and_idempotency(client):
    text='title,description,status,priority\nReview storage,,open,high\n'
    preview=client.post('/api/v1/work-items/import/preview',json={'csv':text}).json()
    body={'csv':text,'fingerprint':preview['fingerprint']};key=str(uuid4())
    a=client.post('/api/v1/work-items/import/commit',json=body,headers={'Idempotency-Key':key})
    b=client.post('/api/v1/work-items/import/commit',json=body,headers={'Idempotency-Key':key})
    assert a.status_code==b.status_code==200 and a.json()==b.json()
    assert client.get('/api/v1/work-items').json()['total']==1
    body['csv']=text.replace('Review storage','Changed')
    assert client.post('/api/v1/work-items/import/commit',json=body,headers={'Idempotency-Key':str(uuid4())}).status_code==422

@pytest.mark.parametrize('csv',['title,title,status,priority\nx,x,open,high\n','title\na','', '# golden-work-items/999\n'])
def test_invalid_columns_and_version(csv):
    with pytest.raises(AppError):preview_csv(csv)

def test_many_rows_rejected():
    with pytest.raises(AppError):preview_csv('title,description,status,priority\n'+'Task,,open,high\n'*101)
