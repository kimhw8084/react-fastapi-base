import { useMemo, useRef, useState } from 'react'
import type { ApiClient } from '../api/client'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'
import { FieldInput } from './FieldInput'
import { parseWorkspaceFieldDraft } from './fieldDraft'
import type { BaseRecord, Draft, WorkspaceAdapter } from './types'

function initialValue(kind:string,choices:readonly string[]):string{
 if(kind==='boolean')return 'false'
 if(kind==='multiselect')return '[]'
 if(kind==='json')return '{}'
 if(kind==='select')return choices[0]??''
 return ''
}
export function BulkEditDialog<T extends BaseRecord>({api,adapter,rows,onClose,onDone}:{api:ApiClient;adapter:WorkspaceAdapter<T>;rows:T[];onClose:()=>void;onDone:(count:number)=>void}){
 const fields=useMemo(()=>adapter.definition.fields.filter(field=>!field.read_only),[adapter.definition.fields])
 const [fieldKey,setFieldKey]=useState(fields[0]?.key??'')
 const field=fields.find(value=>value.key===fieldKey)??fields[0]
 const [draft,setDraft]=useState<Draft>(()=>field?{[field.key]:initialValue(field.kind,field.choices)}:{})
 const [busy,setBusy]=useState(false);const[error,setError]=useState<unknown>(null)
 const operationKey=useRef(crypto.randomUUID())
 const choose=(key:string)=>{const next=fields.find(value=>value.key===key);setFieldKey(key);setDraft(next?{[key]:initialValue(next.kind,next.choices)}:{})}
 const save=async()=>{
  if(!field||!adapter.entityKey)return
  setBusy(true);setError(null)
  try{
   const value=parseWorkspaceFieldDraft(field,String(draft[field.key]??''))
   const result=await api.json<{updated:Array<{id:string}>}>(`/api/v1/entities/${encodeURIComponent(adapter.entityKey)}/bulk-update`,'POST',{targets:rows.map(row=>({id:row.id,revision:row.revision})),patch:{[field.key]:value}},operationKey.current)
   onDone(result.updated.length)
  }catch(value){setError(value)}finally{setBusy(false)}
 }
 const labels=rows.slice(0,12).map(row=>String(row[adapter.definition.primary_field as keyof T]??row.id))
 return <Dialog title={`Bulk edit ${rows.length} ${rows.length===1?adapter.singular:adapter.definition.label.toLowerCase()}`} subtitle="One validated field change is applied atomically to the explicit selection." onClose={onClose} busy={busy} footer={<><span className="muted">Every selected revision is checked before the first write.</span><button disabled={busy} onClick={onClose}>Cancel</button><button className="primary" disabled={busy||!field} onClick={()=>{void save()}}>{busy?'Applying…':'Previewed · Apply change'}</button></>}>
  <div className="form-stack">
   {error!=null&&<ErrorNotice error={error}/>} {!adapter.entityKey&&<p className="field-error">This workspace is not bound to a canonical entity and cannot use generic bulk edit.</p>}
   <label>Field<select value={fieldKey} onChange={event=>choose(event.target.value)}>{fields.map(value=><option key={value.key} value={value.key}>{value.label}</option>)}</select></label>
   {field&&<label><span>New {field.label.toLowerCase()}{field.unit&&<> · {field.unit}</>}</span><FieldInput field={field} draft={draft} onChange={setDraft} invalid={false}/></label>}
   <section className="bulk-edit-preview"><header><strong>Explicit selection</strong><span>{rows.length} records</span></header><div className="bulk-preview-list">{labels.map((label,index)=><span key={`${index}-${label}`}>{label}</span>)}{rows.length>labels.length&&<span>+ {rows.length-labels.length} more</span>}</div><p className="muted">This operation never expands to hidden rows or an implicit filter scope. A validation or revision conflict rolls back the transaction.</p></section>
  </div>
 </Dialog>
}
