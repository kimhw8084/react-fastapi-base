from __future__ import annotations
import csv
import hashlib
import io
import json
from pydantic import ValidationError
from app.platform.errors import AppError
from .schemas import WorkItemCreate, ImportPreview

HEADER = '# golden-work-items/1; formula-escape=apostrophe'
FIELDS = ['title','description','status','priority']

def safe_cell(value: str) -> str:
    # Escape formula and leading apostrophe inputs, reversibly for this versioned format.
    return "'"+value if value and (value[0] in "=+-@'\t\r\n" or value.lstrip().startswith(('=','+','-','@'))) else value

def restore_cell(value: str, versioned: bool) -> str:
    return value[1:] if versioned and value.startswith("'") else value

def export_csv(rows) -> str:
    output=io.StringIO(newline='');output.write(HEADER+'\n')
    writer=csv.DictWriter(output,fieldnames=FIELDS,lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({key:safe_cell(str(getattr(row,key))) for key in FIELDS})
    return output.getvalue()

def preview_csv(content: str) -> ImportPreview:
    if len(content.encode())>500000:
        raise AppError(413,'import_too_large','CSV exceeds the supported preview size.')
    content=content.lstrip('\ufeff')
    versioned=content.startswith(HEADER+'\n') or content.startswith(HEADER+'\r\n')
    if content.startswith('#') and not versioned:
        raise AppError(422,'import_schema','Unsupported CSV schema version.')
    if versioned:
        content=content.split('\n',1)[1]
    rows=[];errors=[]
    try:
        reader=csv.DictReader(io.StringIO(content,newline=''),strict=True)
        if reader.fieldnames is None or len(reader.fieldnames)!=len(FIELDS) or set(reader.fieldnames)!=set(FIELDS):
            raise AppError(422,'import_columns','CSV must contain title, description, status and priority exactly once.')
        for index,row in enumerate(reader,2):
            if index>101:
                raise AppError(413,'import_too_many_rows','Import at most 100 records per reviewed batch.')
            if None in row or any(value is None for value in row.values()):
                errors.append(f'Row {index}: incorrect number of columns.');continue
            try:
                rows.append(WorkItemCreate.model_validate({key:restore_cell(value,versioned) for key,value in row.items()}))
            except ValidationError as error:
                for e in error.errors():
                    errors.append(f'Row {index}, {e["loc"][0]}: {e["msg"]}')
    except csv.Error:
        raise AppError(422,'import_parse','CSV could not be parsed safely.') from None
    fingerprint=hashlib.sha256(json.dumps([row.model_dump() for row in rows],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return ImportPreview(rows=rows,errors=errors,fingerprint=fingerprint)
