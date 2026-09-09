from __future__ import annotations
import csv
import hashlib
import io
import json
import zipfile
from xml.etree import ElementTree
from pydantic import ValidationError
from app.platform.errors import AppError
from .schemas import WorkItemCreate, ImportPreview

HEADER = '# golden-work-items/1; formula-escape=apostrophe'
SNAPSHOT_SCHEMA = 'golden-work-items/1'
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

def export_xlsx(rows) -> bytes:
    """Write a dependency-free, formula-free XLSX workbook for reviewed exchange."""
    namespace='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    def cell(reference: str, value: str) -> ElementTree.Element:
        node=ElementTree.Element(f'{{{namespace}}}c',{'r':reference,'t':'inlineStr'})
        inline=ElementTree.SubElement(node,f'{{{namespace}}}is')
        ElementTree.SubElement(inline,f'{{{namespace}}}t').text=value
        return node
    root=ElementTree.Element(f'{{{namespace}}}worksheet')
    sheet=ElementTree.SubElement(root,f'{{{namespace}}}sheetData')
    values=[[HEADER],FIELDS]+[[safe_cell(str(getattr(row,key))) for key in FIELDS] for row in rows]
    for row_number,values_row in enumerate(values,1):
        row=ElementTree.SubElement(sheet,f'{{{namespace}}}row',{'r':str(row_number)})
        for column,value in enumerate(values_row,1):
            letters='';number=column
            while number:
                number,remainder=divmod(number-1,26);letters=chr(65+remainder)+letters
            row.append(cell(f'{letters}{row_number}',value))
    worksheet=ElementTree.tostring(root,encoding='utf-8',xml_declaration=True)
    workbook=b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Work items" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels=b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    workbook_rels=b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    content_types=b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml',content_types);archive.writestr('_rels/.rels',rels);archive.writestr('xl/workbook.xml',workbook);archive.writestr('xl/_rels/workbook.xml.rels',workbook_rels);archive.writestr('xl/worksheets/sheet1.xml',worksheet)
    return output.getvalue()

def export_json(rows) -> str:
    """Export a bounded, versioned record snapshot without executable content."""
    payload={'schema':SNAPSHOT_SCHEMA,'records':[{key:getattr(row,key) for key in FIELDS} for row in rows]}
    return json.dumps(payload,sort_keys=True,separators=(',',':'))+'\n'

def preview_json(content: str) -> ImportPreview:
    if len(content.encode())>500000:raise AppError(413,'import_too_large','JSON snapshot exceeds the supported preview size.')
    try:payload=json.loads(content)
    except (TypeError,ValueError):raise AppError(422,'import_parse','JSON snapshot could not be parsed safely.') from None
    if not isinstance(payload,dict) or payload.get('schema')!=SNAPSHOT_SCHEMA or not isinstance(payload.get('records'),list):
        raise AppError(422,'import_schema','Unsupported JSON snapshot schema.')
    rows=[];errors=[]
    for index,raw in enumerate(payload['records'],2):
        if index>101:raise AppError(413,'import_too_many_rows','Import at most 100 records per reviewed batch.')
        if not isinstance(raw,dict):errors.append(f'Row {index}: record must be an object.');continue
        try:rows.append(WorkItemCreate.model_validate({key:raw.get(key) for key in FIELDS}))
        except ValidationError as error:
            for item in error.errors():errors.append(f'Row {index}, {item["loc"][0]}: {item["msg"]}')
    fingerprint=hashlib.sha256(json.dumps([row.model_dump() for row in rows],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return ImportPreview(rows=rows,errors=errors,fingerprint=fingerprint)

def preview_xlsx(content: bytes) -> ImportPreview:
    if len(content)>500000:raise AppError(413,'import_too_large','XLSX exceeds the supported preview size.')
    namespace='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if 'xl/worksheets/sheet1.xml' not in archive.namelist():raise AppError(422,'import_schema','XLSX sheet is missing.')
            xml=ElementTree.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    except (zipfile.BadZipFile,ElementTree.ParseError,KeyError):
        raise AppError(422,'import_parse','XLSX could not be parsed safely.') from None
    rows=[]
    for row in xml.findall(f'.//{namespace}row'):
        values=[]
        for cell in row.findall(f'{namespace}c'):
            if cell.find(f'{namespace}f') is not None:raise AppError(422,'import_formula','Formula cells are not accepted in reviewed imports.')
            text=cell.find(f'{namespace}is/{namespace}t')
            values.append(text.text if text is not None and text.text is not None else '')
        rows.append(values)
    if not rows:raise AppError(422,'import_columns','XLSX contains no rows.')
    versioned=bool(rows[0]) and rows[0][0]==HEADER
    if rows[0] and rows[0][0].startswith('#') and not versioned:raise AppError(422,'import_schema','Unsupported XLSX schema version.')
    header=rows[1] if versioned and len(rows)>1 else rows[0];data=rows[2:] if versioned else rows[1:]
    if header!=FIELDS:raise AppError(422,'import_columns','XLSX must contain title, description, status and priority exactly once.')
    parsed=[];errors=[]
    for index,values in enumerate(data,3 if versioned else 2):
        if index>101:raise AppError(413,'import_too_many_rows','Import at most 100 records per reviewed batch.')
        if len(values)!=len(FIELDS):errors.append(f'Row {index}: incorrect number of columns.');continue
        try:parsed.append(WorkItemCreate.model_validate({key:restore_cell(value,versioned) for key,value in zip(FIELDS,values)}))
        except ValidationError as error:
            for item in error.errors():errors.append(f'Row {index}, {item["loc"][0]}: {item["msg"]}')
    fingerprint=hashlib.sha256(json.dumps([row.model_dump() for row in parsed],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return ImportPreview(rows=parsed,errors=errors,fingerprint=fingerprint)
