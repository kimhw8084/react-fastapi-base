import { useCallback, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import type { ReactNode } from 'react'
import type { ViewDefinition } from '../../generated/schema'
import { ErrorNotice, EmptyState } from '../ui/Notice'
import { Dialog } from '../ui/Dialog'
import { WorkspaceShell } from '../ui/WorkspaceShell'
import { RecordForm } from './RecordForm'
import { Dossier } from './Dossier'
import { RecordPeek } from './RecordPeek'
import type { BaseRecord, Draft, WorkspaceAdapter } from './types'
import type { WorkspaceContext } from './context'

interface Props<T extends BaseRecord> extends WorkspaceContext {
 adapter:WorkspaceAdapter<T>
 view:ViewDefinition
 onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void
 searchInput:string
 onSearchInput:(value:string)=>void
 viewTools?:ReactNode
}

function fieldValue<T extends BaseRecord>(row:T,key:string){return (row as unknown as Record<string,unknown>)[key]}

export function BoardWorkspace<T extends BaseRecord>({adapter,api,user,tenant,permissions,view,onViewChange,searchInput,onSearchInput,viewTools}:Props<T>){
 const client=useQueryClient()
 const setView=onViewChange
 const [selection,setSelection]=useState<T[]>([])
 const [peek,setPeek]=useState<T|null>(null)
 const [form,setForm]=useState<T|'new'|null>(null)
 const [confirm,setConfirm]=useState<'archive'|'restore'|null>(null)
 const [notice,setNotice]=useState('')
 const [params,setParams]=useSearchParams()
 const itemId=params.get('item')
 const canWrite=permissions.includes('write')
 const groupFields=adapter.definition.fields.filter(field=>field.choices.length>0&&adapter.definition.filter_keys.includes(field.key))
 const defaultGroupKey=groupFields.find(field=>field.key==='status')?.key??groupFields[0]?.key??''
 const groupKey=view.group_by||defaultGroupKey
 const groupField=groupFields.find(field=>field.key===groupKey)
 const query=useMemo(()=>({search:view.search,filters:view.filters,archived:view.archived,sort:view.sort,direction:view.direction,limit:1000,offset:0}),[view.search,view.filters,view.archived,view.sort,view.direction])
 const records=useQuery({queryKey:['records',user,tenant,adapter.key,'board',query],queryFn:({signal})=>adapter.list(query,signal)})
 const detail=useQuery({queryKey:['detail',user,tenant,adapter.key,itemId],queryFn:()=>adapter.get(itemId??''),enabled:Boolean(itemId)})
 const refresh=useCallback(()=>{void client.invalidateQueries({queryKey:['records',user,tenant,adapter.key]});void client.invalidateQueries({queryKey:['detail',user,tenant,adapter.key]});void client.invalidateQueries({queryKey:['history',user,tenant,adapter.key]});setSelection([])},[client,user,tenant,adapter.key])
 const openRow=(row:T)=>setParams(current=>{const next=new URLSearchParams(current);next.set('item',row.id);return next})
 const closeRow=()=>setParams(current=>{const next=new URLSearchParams(current);next.delete('item');return next})
 const move=useMutation({mutationFn:({row,value}:{row:T;value:string})=>adapter.update(row,{...adapter.draft(row),[groupKey]:value} as Draft),onSuccess:()=>{setNotice('Record moved. All projections now read the updated canonical record.');refresh()}})
 const bulk=useMutation({mutationFn:(action:'archive'|'restore')=>adapter.bulk(selection,action,crypto.randomUUID()),onSuccess:rows=>{setConfirm(null);setNotice(`${rows.length} records changed atomically.`);refresh()}})
 const rows=records.data?.items??[]
 const values=groupField?.choices??[]
 const columns=values.map(value=>({value,rows:rows.filter(row=>String(fieldValue(row,groupKey)??'')===value)}))
 const ungrouped=groupKey?rows.filter(row=>!values.includes(String(fieldValue(row,groupKey)??''))):rows
 const toggle=(row:T,checked:boolean)=>setSelection(current=>checked?[...current.filter(item=>item.id!==row.id),row]:current.filter(item=>item.id!==row.id))
 const primary=adapter.definition.primary_field
 const secondary=adapter.definition.fields.filter(field=>field.key!==primary&&field.key!==groupKey).slice(0,2)
 return <WorkspaceShell eyebrow="Canonical projection" title={`${adapter.definition.label} board`} description={`The board and table operate on the same ${adapter.singular} records. Moving a card creates a normal audited update rather than board-specific shadow data.`} actions={<><button onClick={refresh}>↻ Refresh</button>{canWrite&&<button className="primary" onClick={()=>setForm('new')}>＋ New {adapter.singular}</button>}</>} metrics={[{label:'Matching records',value:records.data?.total??'—'},{label:'Selected',value:selection.length},{label:'Grouping',value:groupField?.label??'None',className:'summary-word'},{label:'Access',value:canWrite?'Editor':'Read only',className:'summary-word'}]} commandBar={<><label className="search-field"><span className="sr-only">Search records</span><span aria-hidden="true">⌕</span><input value={searchInput} maxLength={200} aria-label="Search board records" placeholder={`Search ${adapter.definition.label.toLowerCase()}…`} onChange={event=>onSearchInput(event.target.value)}/></label><div className="segmented" aria-label="Dataset"><button aria-pressed={!view.archived} onClick={()=>setView(current=>({...current,archived:false}))}>Active</button><button aria-pressed={view.archived} onClick={()=>setView(current=>({...current,archived:true}))}>Archived</button></div>{adapter.definition.filter_keys.map(key=>{const field=adapter.definition.fields.find(value=>value.key===key);return field&&field.choices.length?<label key={key}>{field.label}<select aria-label={`Filter board by ${field.label.toLowerCase()}`} value={view.filters[key]??''} onChange={event=>setView(current=>{const filters={...current.filters};if(event.target.value)filters[key]=event.target.value;else delete filters[key];return {...current,filters}})}><option value="">All {field.label.toLowerCase()}</option>{field.choices.map(value=><option key={value} value={value}>{value.replaceAll('_',' ')}</option>)}</select></label>:null})}{groupFields.length>0&&<label>Group cards<select value={groupKey} onChange={event=>setView(current=>({...current,group_by:event.target.value}))}>{groupFields.map(field=><option key={field.key} value={field.key}>{field.label}</option>)}</select></label>}<label>Sort cards<select value={view.sort} onChange={event=>setView(current=>({...current,sort:event.target.value}))}>{adapter.definition.sort_keys.map(key=><option key={key} value={key}>{adapter.definition.fields.find(field=>field.key===key)?.label??key.replaceAll('_',' ')}</option>)}</select></label><button aria-label="Toggle board sort direction" onClick={()=>setView(current=>({...current,direction:current.direction==='asc'?'desc':'asc'}))}>{view.direction==='asc'?'↑ Ascending':'↓ Descending'}</button></>} secondaryBar={<>{viewTools}<div className="toolbar-actions">{selection.length>0&&canWrite&&(!view.archived||permissions.includes('restore'))&&<button className="danger" onClick={()=>setConfirm(view.archived?'restore':'archive')}>{view.archived?'Restore':'Archive'} selected ({selection.length})</button>}</div></>} notice={notice?<div className="notice" role="status">{notice}<button aria-label="Dismiss notification" onClick={()=>setNotice('')}>×</button></div>:undefined}>
  {records.isError&&<ErrorNotice error={records.error} retry={()=>{void records.refetch()}}/>}
  {move.isError&&<ErrorNotice error={move.error}/>} 
  {records.isPending?<div className="loading-state" role="status">Loading board…</div>:!records.isError&&rows.length===0?<EmptyState title="No matching records" description="Adjust search or create the first record."/>:<div className={`board-scroll density-${view.density}`} role="region" aria-label={`${adapter.definition.label} board`}><div className="board-columns">{columns.map(column=><section className="board-column" key={column.value} aria-label={`${column.value} ${adapter.definition.label}`}><header><strong>{column.value.replaceAll('_',' ')}</strong><span>{column.rows.length}</span></header><div className="board-card-list">{column.rows.map(row=><article className="board-card" key={row.id}><div className="board-card-heading"><label className="board-select"><span className="sr-only">Select {String(fieldValue(row,primary)??row.id)}</span><input type="checkbox" checked={selection.some(item=>item.id===row.id)} onChange={event=>toggle(row,event.target.checked)}/></label><button className="board-card-title" onClick={()=>openRow(row)}>{String(fieldValue(row,primary)??row.id)}</button><button className="peek-button" onClick={()=>setPeek(row)} aria-label={`Quick look ${String(fieldValue(row,primary)??row.id)}`}>◫</button></div>{secondary.map(field=><p key={field.key}><span>{field.label}</span>{String(fieldValue(row,field.key)??'—')}</p>)}{canWrite&&!row.archived&&groupField&&<label className="board-move">Move to<select aria-label={`Move ${String(fieldValue(row,primary)??row.id)} to ${groupField.label}`} value={String(fieldValue(row,groupKey)??'')} disabled={move.isPending} onChange={event=>move.mutate({row,value:event.target.value})}>{values.map(value=><option key={value} value={value}>{value.replaceAll('_',' ')}</option>)}</select></label>}</article>)}</div></section>)}{ungrouped.length>0&&<section className="board-column"><header><strong>Other</strong><span>{ungrouped.length}</span></header><div className="board-card-list">{ungrouped.map(row=><article className="board-card" key={row.id}><button className="board-card-title" onClick={()=>openRow(row)}>{String(fieldValue(row,primary)??row.id)}</button></article>)}</div></section>}</div></div>}
  {records.data&&records.data.total>records.data.items.length&&<div className="notice">Showing the first {records.data.items.length} of {records.data.total} records. Narrow search for complete board scope.</div>}
  <RecordPeek adapter={adapter} row={peek} onClose={()=>setPeek(null)} onOpen={row=>{setPeek(null);openRow(row)}} onEdit={canWrite?row=>{setPeek(null);setForm(row)}:undefined}/>
  {itemId&&detail.isError&&<Dialog title="Record unavailable" onClose={closeRow}><ErrorNotice error={detail.error}/></Dialog>}
  {detail.data&&itemId&&form===null&&<Dossier adapter={adapter} api={api} row={detail.data} user={user} tenant={tenant} canWrite={canWrite} canRestore={permissions.includes('restore')} onClose={closeRow} onEdit={canWrite?()=>setForm(detail.data??null):undefined} onChanged={refresh}/>} 
  {form!==null&&<RecordForm adapter={adapter} row={form==='new'?undefined:form} onClose={()=>setForm(null)} onSaved={row=>{setForm(null);refresh();openRow(row)}}/>}
  {confirm&&<Dialog title={`${confirm==='archive'?'Archive':'Restore'} ${selection.length} selected records?`} onClose={()=>setConfirm(null)} busy={bulk.isPending} footer={<><button onClick={()=>setConfirm(null)} disabled={bulk.isPending}>Cancel</button><button className="danger" onClick={()=>bulk.mutate(confirm)} disabled={bulk.isPending}>Confirm change</button></>}><p>Only the explicit board selection is changed. The server applies the batch atomically.</p>{bulk.isError&&<ErrorNotice error={bulk.error}/>}</Dialog>}
 </WorkspaceShell>
}
