import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import type { ViewDefinition } from '../../generated/schema'
import type { WorkspaceContext } from './context'
import type { BaseRecord, WorkspaceAdapter } from './types'
import { WorkspaceShell } from '../ui/WorkspaceShell'
import { ErrorNotice, EmptyState } from '../ui/Notice'
import { Dialog } from '../ui/Dialog'
import { Dossier } from './Dossier'
import { RecordForm } from './RecordForm'
import { RecordPeek } from './RecordPeek'

export interface ProjectionRenderContext<T extends BaseRecord> {
  openRow: (row:T)=>void
  peekRow: (row:T)=>void
  canWrite: boolean
  refresh: ()=>void
}

interface Props<T extends BaseRecord> extends WorkspaceContext {
  adapter: WorkspaceAdapter<T>
  view: ViewDefinition
  onViewChange: (value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void
  searchInput: string
  onSearchInput: (value:string)=>void
  viewTools?: ReactNode
  projectionKey: string
  title: string
  description: string
  children: (rows:T[],context:ProjectionRenderContext<T>)=>ReactNode
  limit?: number
  extraMetrics?: (rows:T[])=>Array<{label:string;value:string|number;className?:string}>
}

export function ProjectionWorkspaceFrame<T extends BaseRecord>({adapter,api,user,tenant,permissions,view,onViewChange,searchInput,onSearchInput,viewTools,projectionKey,title,description,children,limit=500,extraMetrics}:Props<T>){
  const client=useQueryClient()
  const [peek,setPeek]=useState<T|null>(null)
  const [form,setForm]=useState<T|'new'|null>(null)
  const [params,setParams]=useSearchParams()
  const itemId=params.get('item')
  const canWrite=permissions.includes('write')
  const query=useMemo(()=>({search:view.search,filters:view.filters,archived:view.archived,sort:view.sort,direction:view.direction,limit,offset:0}),[view.search,view.filters,view.archived,view.sort,view.direction,limit])
  const records=useQuery({queryKey:['records',user,tenant,adapter.key,projectionKey,query],queryFn:({signal})=>adapter.list(query,signal)})
  const detail=useQuery({queryKey:['detail',user,tenant,adapter.key,itemId],queryFn:()=>adapter.get(itemId??''),enabled:Boolean(itemId)})
  const refresh=useCallback(()=>{void client.invalidateQueries({queryKey:['records',user,tenant,adapter.key]});void client.invalidateQueries({queryKey:['detail',user,tenant,adapter.key]});void client.invalidateQueries({queryKey:['history',user,tenant,adapter.key]})},[client,user,tenant,adapter.key])
  const openRow=(row:T)=>setParams(current=>{const next=new URLSearchParams(current);next.set('item',row.id);return next})
  const closeRow=()=>setParams(current=>{const next=new URLSearchParams(current);next.delete('item');return next})
  const rows=records.data?.items??[]
  const metrics=[{label:'Matching records',value:records.data?.total??'—'},{label:'Visualization',value:projectionKey,className:'summary-word'},{label:'Dataset',value:view.archived?'Archived':'Active',className:'summary-word'},{label:'Access',value:canWrite?'Editor':'Read only',className:'summary-word'},...(extraMetrics?.(rows)??[])]
  return <WorkspaceShell eyebrow="Canonical projection" title={title} description={description} actions={<><button onClick={refresh}>↻ Refresh</button>{canWrite&&<button className="primary" onClick={()=>setForm('new')}>＋ New {adapter.singular}</button>}</>} metrics={metrics} commandBar={<>
    <label className="search-field"><span className="sr-only">Search records</span><span aria-hidden="true">⌕</span><input value={searchInput} maxLength={200} aria-label={`Search ${projectionKey} records`} placeholder={`Search ${adapter.definition.label.toLowerCase()}…`} onChange={event=>onSearchInput(event.target.value)}/></label>
    <div className="segmented" aria-label="Dataset"><button aria-pressed={!view.archived} onClick={()=>onViewChange(current=>({...current,archived:false}))}>Active</button><button aria-pressed={view.archived} onClick={()=>onViewChange(current=>({...current,archived:true}))}>Archived</button></div>
    {adapter.definition.filter_keys.map(key=>{const field=adapter.definition.fields.find(value=>value.key===key);return field&&field.choices.length?<label key={key}>{field.label}<select aria-label={`Filter ${projectionKey} by ${field.label.toLowerCase()}`} value={view.filters[key]??''} onChange={event=>onViewChange(current=>{const filters={...current.filters};if(event.target.value)filters[key]=event.target.value;else delete filters[key];return {...current,filters}})}><option value="">All {field.label.toLowerCase()}</option>{field.choices.map(value=><option key={value} value={value}>{value.replaceAll('_',' ')}</option>)}</select></label>:null})}
  </>} secondaryBar={viewTools}>
    {records.isError&&<ErrorNotice error={records.error} retry={()=>{void records.refetch()}}/>}
    {records.isPending?<div className="loading-state" role="status">Loading {projectionKey}…</div>:!records.isError&&rows.length===0?<EmptyState title="No matching records" description="Adjust the shared workspace filters or create the first record."/>:!records.isError&&children(rows,{openRow,peekRow:setPeek,canWrite,refresh})}
    {records.data&&records.data.total>records.data.items.length&&<div className="notice">Showing {records.data.items.length} of {records.data.total} records in this projection. Narrow shared filters for complete scope.</div>}
    <RecordPeek adapter={adapter} row={peek} onClose={()=>setPeek(null)} onOpen={row=>{setPeek(null);openRow(row)}} onEdit={canWrite?row=>{setPeek(null);setForm(row)}:undefined}/>
    {itemId&&detail.isError&&<Dialog title="Record unavailable" onClose={closeRow}><ErrorNotice error={detail.error}/></Dialog>}
    {detail.data&&itemId&&form===null&&<Dossier adapter={adapter} api={api} row={detail.data} user={user} tenant={tenant} canWrite={canWrite} canRestore={permissions.includes('restore')} onClose={closeRow} onEdit={canWrite?()=>setForm(detail.data??null):undefined} onChanged={refresh}/>} 
    {form!==null&&<RecordForm adapter={adapter} row={form==='new'?undefined:form} onClose={()=>setForm(null)} onSaved={row=>{setForm(null);refresh();openRow(row)}}/>}
  </WorkspaceShell>
}
