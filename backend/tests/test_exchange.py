from uuid import uuid4
import pytest
from app.features.work_items.exchange import export_csv,preview_csv,safe_cell
from app.features.work_items.schemas import WorkItemCreate
from app.platform.errors import AppError

@pytest.mark.parametrize('value',['=SUM(1,2)','+cmd','-42','@danger',"'leading",'plain','회사','  =SUM(A1)','line\nbreak'])
def test_csv_roundtrip_and_formula_safety(value):
    row=WorkItemCreate(title='Title',description=value)
    text=export_csv([row]);preview=preview_csv(text)
    assert preview.errors==[]
    assert preview.rows[0].description==value
    if value.lstrip().startswith(('=','+','-','@')):assert safe_cell(value).startswith("'")

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
