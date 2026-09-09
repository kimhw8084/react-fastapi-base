import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { AttachmentRead } from '../../generated/schema'
import type { ApiClient } from '../api/client'
import { ErrorNotice } from '../ui/Notice'

export function FilesPanel({api,entity,recordId,canWrite,scope}:{api:ApiClient;entity:string;recordId:string;canWrite:boolean;scope:string}){
 const client=useQueryClient();const base=`/api/v1/records/${encodeURIComponent(entity)}/${encodeURIComponent(recordId)}/attachments`;const key=['record-attachments',scope,entity,recordId]
 const files=useQuery({queryKey:key,queryFn:()=>api.request<AttachmentRead[]>(base)})
 const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null)
 const upload=async(file:File)=>{setError(null);if(file.size>1_000_000){setError(new Error('Attachments must be at most 1 MB.'));return}setBusy(true);try{const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);await api.json(base,'POST',{filename:file.name,content_type:file.type,content_base64:btoa(binary)});await client.invalidateQueries({queryKey:key})}catch(value){setError(value)}finally{setBusy(false)}}
 return <section aria-label="Files"><p className="muted">Tenant-scoped files are validated server-side and downloaded as inert attachments.</p>{canWrite&&<label className="form-stack">Attach a file (1 MB maximum)<input type="file" disabled={busy} accept=".txt,.pdf,.png,.jpg,.jpeg" onChange={event=>{const file=event.target.files?.[0];if(file)void upload(file)}}/></label>}{busy&&<p role="status">Uploading…</p>}{error!==null&&<ErrorNotice error={error}/>} {files.isError&&<ErrorNotice error={files.error}/>}<div className="file-list">{files.data?.map(file=><button type="button" key={file.id} onClick={()=>{void api.download(`${base}/${encodeURIComponent(file.id)}`,file.filename).catch(setError)}}><span>{file.filename}</span><span>{Math.ceil(file.size/1024)} KB</span></button>)}</div>{!files.isPending&&!files.data?.length&&<p className="muted">No files attached.</p>}</section>
}
