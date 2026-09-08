import { useRef, useState } from 'react'
import type { ImportPreview, WorkItemRead } from '../../generated/schema'
import type { ApiClient } from '../../platform/api/client'
import { ErrorNotice } from '../../platform/ui/Notice'
import { Dialog } from '../../platform/ui/Dialog'
export function Exchange({ api,onClose,onDone }: { api:ApiClient;onClose:()=>void;onDone:()=>void }) {
  const [csv,setCsv]=useState('');const [preview,setPreview]=useState<ImportPreview|null>(null)
  const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null);const key=useRef(crypto.randomUUID())
  const run=async(commit=false)=>{setBusy(true);setError(null);try{if(commit&&preview){await api.json<WorkItemRead[]>('/api/v1/work-items/import/commit','POST',{csv,fingerprint:preview.fingerprint},key.current);onDone()}else setPreview(await api.json<ImportPreview>('/api/v1/work-items/import/preview','POST',{csv}))}catch(e){setError(e)}finally{setBusy(false)}}
  return <Dialog title="Review CSV import" wide onClose={onClose} dirty={csv.length>0} busy={busy} footer={<><span className="muted">Up to 100 records. Import creates new records; it never silently overwrites.</span><button disabled={busy||!csv} onClick={()=>{void run()}}>Preview</button><button className="primary" disabled={busy||!preview||preview.errors.length>0||preview.rows.length===0} onClick={()=>{void run(true)}}>Import {preview?.rows.length??0} records</button></>}>
    <label className="form-stack">Choose CSV<input type="file" accept=".csv,text/csv" onChange={async e=>{const file=e.target.files?.[0];if(file){if(file.size>500000){setError(new Error('CSV must be smaller than 500 KB.'));return}setCsv(await file.text());setPreview(null);key.current=crypto.randomUUID()}}}/></label>
    <label className="form-stack">Or paste CSV<textarea rows={8} value={csv} spellCheck={false} onChange={e=>{setCsv(e.target.value);setPreview(null);key.current=crypto.randomUUID()}} placeholder="title,description,status,priority"/></label>
    {error!==null&&<ErrorNotice error={error}/>}{preview&&<section aria-label="Import preview"><h3>{preview.rows.length} valid records</h3>{preview.errors.map((message,index)=><p className="field-error" key={index}>{message}</p>)}<div className="preview-list">{preview.rows.map((row,index)=><div key={index}><strong>{row.title}</strong><span>{row.status} · {row.priority}</span></div>)}</div></section>}
  </Dialog>
}
