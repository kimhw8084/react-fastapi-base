import { useRef, useState } from 'react'
import type { ImportPreview, WorkItemRead } from '../../generated/schema'
import type { ApiClient } from '../../platform/api/client'
import { ErrorNotice } from '../../platform/ui/Notice'
import { Dialog } from '../../platform/ui/Dialog'

type ExchangeFormat = 'csv' | 'xlsx' | 'json'
type ExchangeBody = { csv?: string; xlsx_base64?: string; json_snapshot?: string }

function filePayload(file: File, format: ExchangeFormat): Promise<string> {
  if (format !== 'xlsx') return file.text()
  return file.arrayBuffer().then(buffer => {
    let binary = ''
    for (const byte of new Uint8Array(buffer)) binary += String.fromCharCode(byte)
    return btoa(binary)
  })
}

export function Exchange({ api,onClose,onDone }: { api:ApiClient;onClose:()=>void;onDone:()=>void }) {
  const [content,setContent]=useState('');const [format,setFormat]=useState<ExchangeFormat>('csv');const [preview,setPreview]=useState<ImportPreview|null>(null)
  const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);const key=useRef(crypto.randomUUID())
  const body=():ExchangeBody=>format==='csv'?{csv:content}:format==='xlsx'?{xlsx_base64:content}:{json_snapshot:content}
  const run=async(commit=false)=>{setBusy(true);setError(null);try{if(commit&&preview){await api.json<WorkItemRead[]>('/api/v1/work-items/import/commit','POST',{...body(),fingerprint:preview.fingerprint},key.current);onDone()}else setPreview(await api.json<ImportPreview>('/api/v1/work-items/import/preview','POST',body()))}catch(e){setError(e)}finally{setBusy(false)}}
  return <Dialog title={`Review ${format.toUpperCase()} import`} wide onClose={onClose} dirty={content.length>0} busy={busy} footer={<><span className="muted">Up to 100 records. Import creates new records; it never silently overwrites.</span><button disabled={busy||!content} onClick={()=>{void run()}}>Preview</button><button className="primary" disabled={busy||!preview||preview.errors.length>0||preview.rows.length===0} onClick={()=>{void run(true)}}>Import {preview?.rows.length??0} records</button></>}>
    <label className="form-stack">Format<select value={format} onChange={event=>{setFormat(event.target.value as ExchangeFormat);setContent('');setPreview(null);key.current=crypto.randomUUID()}}><option value="csv">CSV</option><option value="xlsx">XLSX</option><option value="json">JSON snapshot</option></select></label>
    <label className="form-stack">Choose {format.toUpperCase()}<input type="file" accept={format==='csv'?'.csv,text/csv':format==='xlsx'?'.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':'.json,application/json'} onChange={async event=>{const file=event.target.files?.[0];if(file){if(file.size>500000){setError(new Error('Exchange files must be smaller than 500 KB.'));return}try{setContent(await filePayload(file,format));setPreview(null);key.current=crypto.randomUUID();setError(null)}catch(value){setError(value)}}}}/></label>
    {format!=='xlsx'&&<label className="form-stack">Or paste {format.toUpperCase()}<textarea rows={8} value={content} spellCheck={false} onChange={event=>{setContent(event.target.value);setPreview(null);key.current=crypto.randomUUID()}} placeholder={format==='csv'?'title,description,status,priority':'{"schema":"golden-work-items/1","records":[]}'}/></label>}
    {error!==null&&<ErrorNotice error={error}/>} {preview&&<section aria-label="Import preview"><h3>{preview.rows.length} valid records</h3>{preview.errors.map((message,index)=><p className="field-error" key={index}>{message}</p>)}<div className="preview-list">{preview.rows.map((row,index)=><div key={index}><strong>{row.title}</strong><span>{row.status} · {row.priority}</span></div>)}</div></section>}
  </Dialog>
}
