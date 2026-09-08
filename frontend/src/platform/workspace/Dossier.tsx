import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'
import type { ApiClient } from '../api/client'
import { Relationships } from './Relationships'
import type { BaseRecord, WorkspaceAdapter } from './types'
import { FieldValue } from './FieldValue'
import { RelatedRecordsExplorer, BacklinksExplorer, DependencyExplorerPanel, ImpactExplorerPanel, ConnectionExplorerPanel } from './Relationships'
import type { CommentRead } from '../../generated/schema'
import { RecordActionMenu } from '../commands/RecordActionMenu'

type DossierTab='overview'|'fields'|'relationships'|'activity'|'history'|'compare'|'comments'|'files'|'audit'|'actions'

export function Dossier<T extends BaseRecord>({ adapter, api, row, tenant, user, canWrite, canRestore, onClose, onEdit, onChanged }: { adapter: WorkspaceAdapter<T>; api: ApiClient; row: T; tenant: string; user: string; canWrite: boolean; canRestore: boolean; onClose: () => void; onEdit?: () => void; onChanged: () => void }) {
  const tabs:readonly DossierTab[]=['overview','fields','relationships','activity','history','compare','comments','files','audit','actions']
  const [tab, setTab] = useState<DossierTab>('overview')
  const history = useQuery({ queryKey: ['history',user,tenant,adapter.key,row.id,row.revision], queryFn: () => adapter.history(row.id), enabled: tab === 'history' || tab === 'compare' })
  const revert = useMutation({ mutationFn: (revision: number) => adapter.revert(row,revision), onSuccess: onChanged })
  const historyRows=history.data??[]
  const revisions=useMemo(()=>[row.revision,...historyRows.map(event=>event.revision).filter(revision=>revision!==row.revision).sort((a,b)=>b-a)],[historyRows,row.revision])
  const [leftRevision,setLeftRevision]=useState(row.revision)
  const [rightRevision,setRightRevision]=useState<number|undefined>(undefined)
  const snapshot=(revision:number):Record<string,unknown>=>{
    if(revision===row.revision)return row as unknown as Record<string,unknown>
    const event=[...historyRows].sort((a,b)=>a.revision-b.revision).find(item=>item.revision===revision)
    return event?.after??{}
  }
  const left=snapshot(leftRevision)
  const right=snapshot(rightRevision??row.revision)
  const changedFields=useMemo(()=>[...new Set([...Object.keys(left),...Object.keys(right)])].filter(key=>JSON.stringify(left[key])!==JSON.stringify(right[key])&&!['created_at','updated_at','revision','id'].includes(key)),[left,right])
  const customTab=(name:'activity'|'comments'|'files'|'audit'|'actions')=>adapter.renderDossierTab?.(name,row)??<p className="muted">This record type has no {name} adapter enabled.</p>
  const comments=useQuery({queryKey:['comments',user,tenant,adapter.entityKey??adapter.key,row.id],queryFn:()=>api.request<CommentRead[]>(`/api/v1/records/${encodeURIComponent(adapter.entityKey??adapter.key)}/${encodeURIComponent(row.id)}/comments`),enabled:tab==='comments'&&Boolean(adapter.entityKey)})
  const [comment,setComment]=useState('')
  const addComment=useMutation({mutationFn:()=>api.json<CommentRead>(`/api/v1/records/${encodeURIComponent(adapter.entityKey??adapter.key)}/${encodeURIComponent(row.id)}/comments`,'POST',{body:comment}),onSuccess:()=>{setComment('');void comments.refetch()}})
  const commentsPanel=<section aria-label="Comments"><form className="form-stack" onSubmit={event=>{event.preventDefault();if(comment.trim())addComment.mutate()}}><label>Add comment<textarea value={comment} maxLength={10000} onChange={event=>setComment(event.target.value)} /></label><button className="primary" disabled={!comment.trim()||addComment.isPending}>Add comment</button></form>{comments.isPending?<p role="status">Loading comments…</p>:comments.isError?<ErrorNotice error={comments.error}/>:comments.data?.length?<div className="comment-list">{comments.data.map(item=><article key={item.id}><header><strong>{item.author}</strong><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></header><p>{item.body}</p></article>)}</div>:<p className="muted">No comments yet.</p>}</section>
  const audit=useQuery({queryKey:['audit',user,tenant,adapter.entityKey??adapter.key,row.id],queryFn:()=>api.request<import('../../generated/schema').AuditRead[]>(`/api/v1/audit?${new URLSearchParams({workspace:adapter.entityKey??adapter.key,entity_id:row.id})}`),enabled:tab==='audit'})
  const auditPanel=<section aria-label="Audit"><p className="muted">Immutable server audit for this record.</p>{audit.isPending?<p role="status">Loading audit…</p>:audit.isError?<ErrorNotice error={audit.error}/>:audit.data?.length?<div className="history-entry">{audit.data.map(item=><article key={item.id}><strong>{item.action} · revision {item.revision}</strong><span>{item.actor} · {new Date(item.created_at).toLocaleString()}</span></article>)}</div>:<p>No audit events.</p>}</section>
  const historyPanel=<section aria-label="Version history"><div className="history-toolbar"><span className="muted">{historyRows.length} audited revisions</span>{history.isError&&<ErrorNotice error={history.error}/>}</div>{history.isPending&&<p role="status">Loading version history…</p>}{historyRows.map(event=><article className="history-entry" key={event.id}><header><strong>Revision {event.revision} · {event.action}</strong><span>{event.actor} · {new Date(event.created_at).toLocaleString()}</span></header><dl className="changes">{Object.keys(event.after??{}).filter(key=>JSON.stringify(event.before?.[key])!==JSON.stringify(event.after?.[key])&&!['created_at','updated_at','revision','id'].includes(key)).map(key=><div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd><del>{String(event.before?.[key]??'—')}</del> → <span>{String(event.after?.[key]??'—')}</span></dd></div>)}</dl>{canRestore&&!row.archived&&event.revision!==row.revision&&<button disabled={revert.isPending} onClick={()=>{if(window.confirm('Revert record fields to this version? This creates a new audited revision.'))revert.mutate(event.revision)}}>Revert to this version</button>}</article>)}</section>
  return <Dialog title={String(row[adapter.definition.primary_field as keyof T]??row.id)} subtitle={`${adapter.singular} · revision ${row.revision}`} status={row.archived?<span className="status-chip">Archived</span>:undefined} wide expandable onClose={onClose} footer={<><span className="muted">Revision {row.revision}{row.archived ? ' · Archived / read-only' : ''}</span><RecordActionMenu adapter={adapter} row={row} permissions={[...(canWrite?['write']:[]),...(canRestore?['restore']:[]),'read']} placement="dossier" callbacks={{open:onClose,peek:onClose,edit:onEdit,copyLink:()=>{void navigator.clipboard.writeText(window.location.href)},history:()=>setTab('history')}}/></>}>
    <div className="segmented" aria-label="Record sections">{tabs.map(name=><button key={name} aria-pressed={tab===name} onClick={()=>setTab(name)}>{name[0]?.toUpperCase()}{name.slice(1)}</button>)}</div>
    {revert.isError&&<ErrorNotice error={revert.error}/>} 
    {tab==='overview'&&(adapter.renderDetails?.(row)??<dl className="record-details">{adapter.definition.fields.filter(field=>field.key===adapter.definition.primary_field||field.read_only).map(field=><div key={field.key}><dt>{field.label}</dt><dd><FieldValue field={field} value={row[field.key as keyof T]}/></dd></div>)}</dl>)}
    {tab==='fields'&&<dl className="record-details">{adapter.definition.fields.map(field=><div key={field.key}><dt>{field.label}</dt><dd><FieldValue field={field} value={row[field.key as keyof T]}/></dd></div>)}</dl>}
    {tab==='relationships'&&<div className="dossier-relationships"><Relationships api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user} canWrite={canWrite} readOnly={row.archived}/><div className="relationship-explorer-grid"><RelatedRecordsExplorer api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/><BacklinksExplorer api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/><DependencyExplorerPanel api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/><ImpactExplorerPanel api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/><ConnectionExplorerPanel api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/></div></div>}
    {tab==='activity'&&<div><p className="muted">Activity is the record’s immutable lifecycle and revision stream.</p>{historyPanel}</div>}
    {tab==='history'&&historyPanel}
    {tab==='compare'&&<section aria-label="Compare revisions" className="revision-compare"><div className="compare-controls"><label>Earlier revision<select value={leftRevision} onChange={event=>setLeftRevision(Number(event.target.value))}>{revisions.map(revision=><option key={revision} value={revision}>Revision {revision}</option>)}</select></label><label>Later revision<select value={rightRevision??row.revision} onChange={event=>setRightRevision(Number(event.target.value))}>{revisions.map(revision=><option key={revision} value={revision}>Revision {revision}</option>)}</select></label></div>{leftRevision===(rightRevision??row.revision)?<p className="muted">Choose two different revisions to compare.</p>:changedFields.length?<dl className="changes">{changedFields.map(key=><div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd><del>{String(left[key]??'—')}</del> → <span>{String(right[key]??'—')}</span></dd></div>)}</dl>:<p>No field changes between these revisions.</p>}</section>}
    {tab==='comments'&&(adapter.entityKey?commentsPanel:customTab('comments'))}
    {tab==='files'&&(adapter.renderAttachments?.(row)??customTab('files'))}
    {tab==='audit'&&auditPanel}
    {tab==='actions'&&customTab('actions')}
  </Dialog>
}
