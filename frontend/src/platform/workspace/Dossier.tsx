import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Dialog } from '../ui/Dialog'
import { ErrorNotice } from '../ui/Notice'
import type { ApiClient } from '../api/client'
import { Relationships } from './Relationships'
import type { BaseRecord, WorkspaceAdapter } from './types'
import { FieldValue } from './FieldValue'

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
  const historyPanel=<section aria-label="Version history"><div className="history-toolbar"><span className="muted">{historyRows.length} audited revisions</span>{history.isError&&<ErrorNotice error={history.error}/>}</div>{history.isPending&&<p role="status">Loading version history…</p>}{historyRows.map(event=><article className="history-entry" key={event.id}><header><strong>Revision {event.revision} · {event.action}</strong><span>{event.actor} · {new Date(event.created_at).toLocaleString()}</span></header><dl className="changes">{Object.keys(event.after??{}).filter(key=>JSON.stringify(event.before?.[key])!==JSON.stringify(event.after?.[key])&&!['created_at','updated_at','revision','id'].includes(key)).map(key=><div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd><del>{String(event.before?.[key]??'—')}</del> → <span>{String(event.after?.[key]??'—')}</span></dd></div>)}</dl>{canRestore&&!row.archived&&event.revision!==row.revision&&<button disabled={revert.isPending} onClick={()=>{if(window.confirm('Revert record fields to this version? This creates a new audited revision.'))revert.mutate(event.revision)}}>Revert to this version</button>}</article>)}</section>
  return <Dialog title={String(row[adapter.definition.primary_field as keyof T]??row.id)} subtitle={`${adapter.singular} · revision ${row.revision}`} status={row.archived?<span className="status-chip">Archived</span>:undefined} wide expandable onClose={onClose} footer={<><span className="muted">Revision {row.revision}{row.archived ? ' · Archived / read-only' : ''}</span><button onClick={() => { void navigator.clipboard.writeText(window.location.href) }}>Copy link</button>{onEdit && !row.archived && <button className="primary" onClick={onEdit}>Edit record</button>}</>}>
    <div className="segmented" aria-label="Record sections">{tabs.map(name=><button key={name} aria-pressed={tab===name} onClick={()=>setTab(name)}>{name[0]?.toUpperCase()}{name.slice(1)}</button>)}</div>
    {revert.isError&&<ErrorNotice error={revert.error}/>} 
    {tab==='overview'&&(adapter.renderDetails?.(row)??<dl className="record-details">{adapter.definition.fields.filter(field=>field.key===adapter.definition.primary_field||field.read_only).map(field=><div key={field.key}><dt>{field.label}</dt><dd><FieldValue field={field} value={row[field.key as keyof T]}/></dd></div>)}</dl>)}
    {tab==='fields'&&<dl className="record-details">{adapter.definition.fields.map(field=><div key={field.key}><dt>{field.label}</dt><dd><FieldValue field={field} value={row[field.key as keyof T]}/></dd></div>)}</dl>}
    {tab==='relationships'&&<Relationships api={api} entity={adapter.entityKey??adapter.key} recordId={row.id} tenant={tenant} user={user} canWrite={canWrite} readOnly={row.archived}/>} 
    {tab==='activity'&&customTab('activity')}
    {tab==='history'&&historyPanel}
    {tab==='compare'&&<section aria-label="Compare revisions" className="revision-compare"><div className="compare-controls"><label>Earlier revision<select value={leftRevision} onChange={event=>setLeftRevision(Number(event.target.value))}>{revisions.map(revision=><option key={revision} value={revision}>Revision {revision}</option>)}</select></label><label>Later revision<select value={rightRevision??row.revision} onChange={event=>setRightRevision(Number(event.target.value))}>{revisions.map(revision=><option key={revision} value={revision}>Revision {revision}</option>)}</select></label></div>{leftRevision===(rightRevision??row.revision)?<p className="muted">Choose two different revisions to compare.</p>:changedFields.length?<dl className="changes">{changedFields.map(key=><div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd><del>{String(left[key]??'—')}</del> → <span>{String(right[key]??'—')}</span></dd></div>)}</dl>:<p>No field changes between these revisions.</p>}</section>}
    {tab==='comments'&&customTab('comments')}
    {tab==='files'&&(adapter.renderAttachments?.(row)??customTab('files'))}
    {tab==='audit'&&customTab('audit')}
    {tab==='actions'&&customTab('actions')}
  </Dialog>
}
