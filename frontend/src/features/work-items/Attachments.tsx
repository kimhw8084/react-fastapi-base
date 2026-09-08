import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { AttachmentRead } from '../../generated/schema'
import type { ApiClient } from '../../platform/api/client'
import { ErrorNotice } from '../../platform/ui/Notice'
export function Attachments({api,itemId,canWrite,scope}:{api:ApiClient;itemId:string;canWrite:boolean;scope:string}){
 const client=useQueryClient();const key=['attachments',scope,itemId];const base=`/api/v1/work-items/${encodeURIComponent(itemId)}/attachments`
 const query=useQuery({queryKey:key,queryFn:()=>api.request<AttachmentRead[]>(base)})
 const [busy,setBusy]=useState(false);const [error,setError]=useState<unknown>(null)
 const upload=async(file:File)=>{setError(null);if(file.size>1_000_000){setError(new Error('Attachments must be at most 1 MB.'));return}setBusy(true);try{const buffer=new Uint8Array(await file.arrayBuffer());let binary='';for(const byte of buffer)binary+=String.fromCharCode(byte);await api.json(base,'POST',{filename:file.name,content_type:file.type,content_base64:btoa(binary)});await client.invalidateQueries({queryKey:key})}catch(e){setError(e)}finally{setBusy(false)}}
 return <section><p className="muted">Private files share the record’s tenant boundary. Downloads are attachments, never inline executable content.</p>{canWrite&&<label className="form-stack">Attach a file (1 MB maximum)<input type="file" disabled={busy} accept=".txt,.pdf,.png,.jpg,.jpeg" onChange={e=>{const f=e.target.files?.[0];if(f)void upload(f)}}/></label>}{busy&&<p role="status">Uploading…</p>}{error!==null&&<ErrorNotice error={error}/>} {query.isError&&<ErrorNotice error={query.error}/>}<div className="file-list">{query.data?.map(file=><button key={file.id} onClick={()=>{void api.download(`${base}/${file.id}`,file.filename).catch(setError)}}><span>{file.filename}</span><span>{Math.ceil(file.size/1024)} KB</span></button>)}</div></section>
}
