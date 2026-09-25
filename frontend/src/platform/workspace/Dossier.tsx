import { useMemo, useState, type ReactNode } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'
import type { ApiClient } from '../api/client'
import { Relationships } from './Relationships'
import type { BaseRecord, WorkspaceAdapter } from './types'
import { FieldValue, fieldLabel } from './FieldValue'
import { RelatedRecordsExplorer, BacklinksExplorer, DependencyExplorerPanel, ImpactExplorerPanel, ConnectionExplorerPanel } from './Relationships'
import type { CommentRead, FieldDefinition } from '../../generated/schema'
import { RecordActionMenu } from '../commands/RecordActionMenu'
import { FilesPanel } from './FilesPanel'
import { revealHorizontalFocus } from '../ui/focusReveal'

type DossierTab='overview'|'fields'|'relationships'|'activity'|'history'|'compare'|'comments'|'files'|'audit'|'actions'

export function dossierTabFallbackText(name:'activity'|'comments'|'files'|'audit'|'actions'):string{
 const copy={
  activity:'No additional record-specific activity is available.',
  comments:'No record-specific comments are available.',
  files:'No record-specific files are available.',
  audit:'No record-specific audit entries are available.',
  actions:'No additional record-specific actions are available.',
 }
 return copy[name]
}

export function formatComparisonValue(value: unknown): { kind: 'empty'|'text'|'structured'; text: string } {
  if (value === null || value === undefined || value === '') return { kind: 'empty', text: '—' }
  if (typeof value === 'string') return { kind: 'text', text: value }
  try { return { kind: 'structured', text: JSON.stringify(value, null, 2) } }
  catch { return { kind: 'text', text: String(value) }
  }
}

function ComparisonValue({ value, deleted = false, field }: { value: unknown; deleted?: boolean; field?:FieldDefinition }): ReactNode {
  if(field&&!['json','object','array','code','markdown','formula','computed','range','tolerance'].includes(field.kind))return <span className={deleted?'comparison-value deleted':'comparison-value'}><FieldValue field={field} value={value}/></span>
  const formatted = formatComparisonValue(value)
  if (formatted.kind === 'structured') return <pre className={deleted ? 'comparison-value deleted' : 'comparison-value'}>{formatted.text}</pre>
  return <span className={deleted ? 'comparison-value deleted' : 'comparison-value'}>{formatted.text}</span>
}

function RecordFieldValue({definition,fieldKey,value}:{definition:WorkspaceAdapter<BaseRecord>['definition'];fieldKey:string;value:unknown}){
 const field=definition.fields.find(item=>item.key===fieldKey)
 return field?<FieldValue field={field} value={value}/>:<span>{value==null||value===''?'—':String(value)}</span>
}

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
  const customTab=(name:'activity'|'comments'|'files'|'audit'|'actions')=>adapter.renderDossierTab?.(name,row)??<p className="muted">{dossierTabFallbackText(name)}</p>
  const comments=useQuery({queryKey:['comments',user,tenant,adapter.entityKey??adapter.key,row.id],queryFn:()=>api.request<CommentRead[]>(`/api/v1/records/${encodeURIComponent(adapter.entityKey??adapter.key)}/${encodeURIComponent(row.id)}/comments`),enabled:tab==='comments'&&Boolean(adapter.entityKey)})
  const [comment,setComment]=useState('')
  const addComment=useMutation({mutationFn:()=>api.json<CommentRead>(`/api/v1/records/${encodeURIComponent(adapter.entityKey??adapter.key)}/${encodeURIComponent(row.id)}/comments`,'POST',{body:comment}),onSuccess:()=>{setComment('');void comments.refetch()}})
  const commentsPanel=<section aria-label="Comments">{canWrite&&!row.archived?<form className="form-stack" onSubmit={event=>{event.preventDefault();if(comment.trim())addComment.mutate()}}><label>Add comment<textarea value={comment} maxLength={10000} onChange={event=>setComment(event.target.value)} /></label><button className="primary" disabled={!comment.trim()||addComment.isPending}>Add comment</button></form>:<p className="notice" role="status">Comments are read-only for this record.</p>}{comments.isPending?<p role="status">Loading comments…</p>:comments.isError?<ErrorNotice error={comments.error}/>:comments.data?.length?<div className="comment-list">{comments.data.map(item=><article key={item.id}><header><strong>{item.author}</strong><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></header><p>{item.body}</p></article>)}</div>:<p className="muted">No comments yet.</p>}</section>
  const audit=useQuery({queryKey:['audit',user,tenant,adapter.entityKey??adapter.key,row.id],queryFn:()=>api.request<import('../../generated/schema').AuditRead[]>(`/api/v1/audit?${new URLSearchParams({workspace:adapter.entityKey??adapter.key,entity_id:row.id})}`),enabled:tab==='audit'})
  const auditPanel=<section aria-label="Audit"><p className="muted">Immutable server audit for this record.</p>{audit.isPending?<p role="status">Loading audit…</p>:audit.isError?<ErrorNotice error={audit.error}/>:audit.data?.length?<div className="history-entry">{audit.data.map(item=><article key={item.id}><strong>{item.action} · revision {item.revision}</strong><span>{item.actor} · {new Date(item.created_at).toLocaleString()}</span></article>)}</div>:<p>No audit events.</p>}</section>
  const historyPanel=<section aria-label="Version history"><div className="history-toolbar"><span className="muted">{historyRows.length} audited revisions</span>{history.isError&&<ErrorNotice error={history.error}/>}</div>{history.isPending&&<p role="status">Loading version history…</p>}{historyRows.map(event=><article className="history-entry" key={event.id}><header><strong>Revision {event.revision} · {event.action}</strong><span>{event.actor} · {new Date(event.created_at).toLocaleString()}</span></header><dl className="changes">{Object.keys(event.after??{}).filter(key=>JSON.stringify(event.before?.[key])!==JSON.stringify(event.after?.[key])&&!['created_at','updated_at','revision','id'].includes(key)).map(key=><div key={key}><dt>{fieldLabel(adapter.definition,key)}</dt><dd><del><RecordFieldValue definition={adapter.definition} fieldKey={key} value={event.before?.[key]}/></del> → <RecordFieldValue definition={adapter.definition} fieldKey={key} value={event.after?.[key]}/></dd></div>)}</dl>{canRestore&&!row.archived&&event.revision!==row.revision&&<button disabled={revert.isPending} onClick={()=>{if(window.confirm('Revert record fields to this version? This creates a new audited revision.'))revert.mutate(event.revision)}}>Revert to this version</button>}</article>)}</section>
  return <Dialog title={String(row[adapter.definition.primary_field as keyof T]??row.id)} subtitle={`${adapter.singular} · revision ${row.revision}`} status={row.archived?<span className="status-chip">Archived</span>:undefined} wide expandable onClose={onClose} footer={<><span className="muted">Revision {row.revision}{row.archived ? ' · Archived / read-only' : ''}</span><RecordActionMenu adapter={adapter} row={row} permissions={[...(canWrite?['write']:[]),...(canRestore?['restore']:[]),'read']} placement="dossier" callbacks={{open:onClose,peek:onClose,edit:onEdit,copyLink:()=>{void navigator.clipboard.writeText(window.location.href)},history:()=>setTab('history')}}/></>}>
    <label className="dossier-mobile-section-select">Record section<select aria-label="Record section" value={tab} onChange={event=>setTab(event.target.value as DossierTab)}>{tabs.map(name=><option key={name} value={name}>{name[0]?.toUpperCase()}{name.slice(1)}</option>)}</select></label>
    <div className="segmented dossier-section-tabs" role="tablist" aria-label="Record sections" onFocusCapture={event=>{if(event.target instanceof HTMLElement)revealHorizontalFocus(event.currentTarget,event.target)}}>{tabs.map(name=><button type="button" role="tab" key={name} aria-selected={tab===name} onClick={()=>setTab(name)}>{name[0]?.toUpperCase()}{name.slice(1)}</button>)}</div>
    {revert.isError&&<ErrorNotice error={revert.error}/>} 
    {tab==='overview'&&(adapter.renderDetails?.(row)??<dl className="record-details">{adapter.definition.fields.filter(field=>field.key===adapter.definition.primary_field||field.read_only).map(field=><div key={field.key}><dt>{field.label}</dt><dd><FieldValue field={field} value={row[field.key as keyof T]}/></dd></div>)}</dl>)}
    {tab==='fields'&&<dl className="record-details">{adapter.definition.fields.map(field=><div key={field.key}><dt>{field.label}</dt><dd><FieldValue field={field} value={row[field.key as keyof T]}/></dd></div>)}</dl>}
    {tab==='relationships'&&<div className="dossier-relationships"><Relationships api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user} canWrite={canWrite} readOnly={row.archived}/><div className="relationship-explorer-grid"><RelatedRecordsExplorer api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/><BacklinksExplorer api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/><DependencyExplorerPanel api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/><ImpactExplorerPanel api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/><ConnectionExplorerPanel api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user}/></div></div>}
    {tab==='activity'&&<div><p className="muted">Activity is the record’s immutable lifecycle and revision stream.</p>{historyPanel}</div>}
    {tab==='history'&&historyPanel}
    {tab==='compare'&&<section aria-label="Compare revisions" className="revision-compare"><div className="compare-controls"><label>Earlier revision<select value={leftRevision} onChange={event=>setLeftRevision(Number(event.target.value))}>{revisions.map(revision=><option key={revision} value={revision}>Revision {revision}</option>)}</select></label><label>Later revision<select value={rightRevision??row.revision} onChange={event=>setRightRevision(Number(event.target.value))}>{revisions.map(revision=><option key={revision} value={revision}>Revision {revision}</option>)}</select></label></div>{leftRevision===(rightRevision??row.revision)?<p className="muted">Choose two different revisions to compare.</p>:changedFields.length?<dl className="changes">{changedFields.map(key=><div key={key}><dt>{fieldLabel(adapter.definition,key)}</dt><dd><ComparisonValue field={adapter.definition.fields.find(field=>field.key===key)} value={left[key]} deleted/> <span aria-hidden="true">→</span> <ComparisonValue field={adapter.definition.fields.find(field=>field.key===key)} value={right[key]}/></dd></div>)}</dl>:<p>No field changes between these revisions.</p>}</section>}
    {tab==='comments'&&(adapter.entityKey?commentsPanel:customTab('comments'))}
    {tab==='files'&&(adapter.renderAttachments?.(row)??(adapter.entityKey?<FilesPanel api={api} entity={adapter.entityKey} recordId={row.id} canWrite={canWrite&&!row.archived} scope={`${user}:${tenant}`}/>:customTab('files')))}
    {tab==='audit'&&auditPanel}
    {tab==='actions'&&customTab('actions')}
  </Dialog>
}
