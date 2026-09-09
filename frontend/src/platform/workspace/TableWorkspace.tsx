import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import type { MatchingBulkPreview, ViewDefinition } from '../../generated/schema'
import { ErrorNotice, EmptyState } from '../ui/Notice'
import { Dialog } from '../ui/Dialog'
import { WorkspaceShell } from '../ui/WorkspaceShell'
import { DataGrid, type GridAnchor } from '../grid/DataGrid'
import { RecordForm } from './RecordForm'
import { Dossier } from './Dossier'
import { RecordPeek } from './RecordPeek'
import { TableDisplayControls } from './TableDisplayControls'
import { TableContextMenu } from './TableContextMenu'
import { RecordActionMenu } from '../commands/RecordActionMenu'
import { actionContext, createRecordActionRegistry } from '../commands/recordActions'
import { useActiveActionSurface } from '../commands/ActionSurfaceContext'
import { HoverRecordPreview } from './HoverRecordPreview'
import { BulkEditDialog } from './BulkEditDialog'
import { viewToListQuery } from './query'
import { type BaseRecord, type WorkspaceAdapter, type ListQuery } from './types'
import type { WorkspaceContext } from './context'

interface Props<T extends BaseRecord> extends WorkspaceContext {
  adapter:WorkspaceAdapter<T>
  view:ViewDefinition
  onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void
  searchInput:string
  onSearchInput:(value:string)=>void
  viewTools?:ReactNode
}
interface AnchoredRecord<T>{row:T;anchor:GridAnchor}
interface MatchingScope { view:ViewDefinition; preview:MatchingBulkPreview }

export function TableWorkspace<T extends BaseRecord>({adapter,api,tenant,user,permissions,view,onViewChange,searchInput,onSearchInput,viewTools}:Props<T>){
  const client=useQueryClient()
  const setView=onViewChange
  const [offset,setOffset]=useState(0)
  const [selection,setSelection]=useState<T[]>([])
  const [peek,setPeek]=useState<T|null>(null)
  const [hover,setHover]=useState<AnchoredRecord<T>|null>(null)
  const hoverTimer=useRef<ReturnType<typeof setTimeout>|null>(null)
  const [context,setContext]=useState<AnchoredRecord<T>|null>(null)
  const [displayAnchor,setDisplayAnchor]=useState<GridAnchor|null>(null)
  const [form,setForm]=useState<T|'new'|null>(null)
  const [exchange,setExchange]=useState(false)
  const [confirm,setConfirm]=useState<'archive'|'restore'|null>(null)
  const [bulkEdit,setBulkEdit]=useState(false)
  const [matchingScope,setMatchingScope]=useState<MatchingScope|null>(null)
  const [notice,setNotice]=useState('')
  const [params,setParams]=useSearchParams()
  const itemId=params.get('item')
  const canWrite=permissions.includes('write')
  const canRestore=permissions.includes('restore')
  const recordLabel=useCallback((row:T)=>String(row[adapter.definition.primary_field as keyof T]??row.id),[adapter.definition])
  useEffect(()=>{setOffset(0)},[view.search])
  useEffect(()=>{
    const handler=(event:KeyboardEvent)=>{
      if(!selection.length||event.defaultPrevented||event.metaKey||event.ctrlKey||event.altKey)return
      if(event.key.toLocaleLowerCase()==='e'&&selection.length===1&&canWrite){event.preventDefault();setForm(selection[0]!)}
    }
    window.addEventListener('keydown',handler)
    return()=>window.removeEventListener('keydown',handler)
  },[canWrite,selection])
  useEffect(()=>()=>{if(hoverTimer.current)clearTimeout(hoverTimer.current)},[])
  const query=useMemo<ListQuery>(()=>viewToListQuery(view,offset,50),[view,offset])
  const scope=JSON.stringify([tenant,adapter.key,query,view.group_by])
  const prefix=['records',user,tenant,adapter.key]
  const records=useQuery({queryKey:[...prefix,query],queryFn:({signal})=>adapter.list(query,signal)})
  const detail=useQuery({queryKey:['detail',user,tenant,adapter.key,itemId],queryFn:()=>adapter.get(itemId??''),enabled:Boolean(itemId)})
  const refresh=useCallback(()=>{void client.invalidateQueries({queryKey:['records',user,tenant,adapter.key]});void client.invalidateQueries({queryKey:['detail',user,tenant,adapter.key]});void client.invalidateQueries({queryKey:['history',user,tenant,adapter.key]});setSelection([])},[client,user,tenant,adapter.key])
  const openRow=useCallback((row:T)=>{setParams(current=>{const next=new URLSearchParams(current);next.set('item',row.id);return next})},[setParams])
  const closeRow=()=>setParams(current=>{const next=new URLSearchParams(current);next.delete('item');return next})
  const bulk=useMutation({mutationFn:(action:'archive'|'restore')=>adapter.bulk(selection,action,crypto.randomUUID()),onSuccess:rows=>{setConfirm(null);setNotice(`${rows.length} records changed. The entire explicit selection was applied atomically.`);refresh()}})
  const matchingPreview=useMutation({mutationFn:()=>{if(!adapter.previewMatching)return Promise.reject(new Error('Matching selection is unavailable for this workspace.'));return adapter.previewMatching(view)},onSuccess:preview=>setMatchingScope({view,preview})})
  const matchingApply=useMutation({mutationFn:({scope,action}:{scope:MatchingScope;action:'archive'|'restore'})=>adapter.bulkMatching!(scope.view,action,scope.preview.total,scope.preview.fingerprint,crypto.randomUUID()),onSuccess:rows=>{setMatchingScope(null);setNotice(`${rows.length} records changed across the reviewed matching query.`);refresh()}})
  const transition=useMutation({mutationFn:({row,action}:{row:T;action:'archive'|'restore'})=>adapter.transition(row,action),onSuccess:(_,variables)=>{setNotice(`${recordLabel(variables.row)} ${variables.action==='archive'?'archived':'restored'}.`);refresh()}})
  const exportData=useMutation({mutationFn:()=>adapter.export(query)})
  const handleHover=useCallback((row:T,anchor:GridAnchor|null)=>{
    if(hoverTimer.current){clearTimeout(hoverTimer.current);hoverTimer.current=null}
    if(!anchor){setHover(null);return}
    hoverTimer.current=setTimeout(()=>setHover({row,anchor}),320)
  },[])
  const copyLink=useCallback(async(row:T)=>{try{const url=new URL(window.location.href);url.searchParams.set('item',row.id);await navigator.clipboard.writeText(url.toString());setNotice('Record link copied.')}catch{setNotice('Could not copy the record link in this browser.')}},[])
  const displayButton=(event:React.MouseEvent<HTMLButtonElement>)=>{const rect=event.currentTarget.getBoundingClientRect();setDisplayAnchor({x:rect.right-340,y:rect.bottom+8})}
  const selectedLabels=selection.slice(0,8).map(recordLabel)
  const paletteRow=selection[0]??null
  const paletteCallbacks=useMemo(()=>paletteRow?{open:()=>openRow(paletteRow),peek:()=>setPeek(paletteRow),edit:canWrite?()=>setForm(paletteRow):undefined,copyLink:()=>{void copyLink(paletteRow)},history:()=>openRow(paletteRow),transition:(action:'archive'|'restore')=>transition.mutate({row:paletteRow,action}),bulkEdit:canWrite&&adapter.entityKey?()=>setBulkEdit(true):undefined}:null,[adapter.entityKey,canWrite,copyLink,openRow,paletteRow,transition])
  const paletteRegistry=useMemo(()=>paletteRow&&paletteCallbacks?createRecordActionRegistry(adapter,paletteRow,paletteCallbacks,[...(canWrite?['write']:[]),...(canRestore?['restore']:[]),'read'],selection.length):null,[adapter,canRestore,canWrite,paletteCallbacks,paletteRow,selection.length])
  const paletteContext=useMemo(()=>paletteRegistry?actionContext(adapter as unknown as Pick<WorkspaceAdapter<BaseRecord>,'key'|'entityKey'>,[...(canWrite?['write']:[]),...(canRestore?['restore']:[]),'read'],selection.length,'palette'):null,[adapter,canRestore,canWrite,paletteRegistry,selection.length])
  useActiveActionSurface(paletteRegistry,paletteContext)
  return <WorkspaceShell eyebrow="Company workspace" title={adapter.definition.label} description={adapter.definition.description} actions={<><button onClick={refresh} aria-label="Refresh workspace">↻ Refresh</button>{canWrite&&<button className="primary" onClick={()=>setForm('new')}>＋ New {adapter.singular}</button>}</>} metrics={[{label:'Matching records',value:records.data?.total??'—'},{label:'Selected on this page',value:selection.length},{label:'Dataset',value:view.archived?'Archived':'Active',className:'summary-word'},{label:'Access',value:canWrite?'Editor':'Read only',className:'summary-word'}]} commandBar={<>
      <label className="search-field"><span className="sr-only">Search records</span><span aria-hidden="true">⌕</span><input aria-label="Search records" value={searchInput} maxLength={200} placeholder={`Search ${adapter.definition.label.toLowerCase()}…`} onChange={event=>onSearchInput(event.target.value)}/></label>
      <div className="segmented" aria-label="Dataset"><button aria-pressed={!view.archived} onClick={()=>{setView({...view,archived:false});setOffset(0)}}>Active</button><button aria-pressed={view.archived} onClick={()=>{setView({...view,archived:true});setOffset(0)}}>Archived</button></div>
      {adapter.definition.filter_keys.map(key=>{const field=adapter.definition.fields.find(value=>value.key===key);return field?<label key={key}>{field.label}<select aria-label={`Filter by ${field.label.toLowerCase()}`} value={view.filters[key]??''} onChange={event=>{const filters={...view.filters};if(event.target.value)filters[key]=event.target.value;else delete filters[key];setView({...view,filters});setOffset(0)}}><option value="">All {field.label.toLowerCase()}</option>{field.choices.map(value=><option value={value} key={value}>{value.replaceAll('_',' ')}</option>)}</select></label>:null})}
      <label>Sort all results<select aria-label="Sort all results" value={view.sort} onChange={event=>{setView({...view,sort:event.target.value});setOffset(0)}}>{adapter.definition.sort_keys.map(key=><option key={key} value={key}>{adapter.definition.fields.find(field=>field.key===key)?.label??key.replaceAll('_',' ')}</option>)}</select></label>
      <button aria-label="Toggle sort direction" onClick={()=>setView({...view,direction:view.direction==='asc'?'desc':'asc'})}>{view.direction==='asc'?'↑ Ascending':'↓ Descending'}</button>
      <button aria-expanded={Boolean(displayAnchor)} onClick={displayButton}>▦ Display{view.group_by?` · ${adapter.definition.fields.find(field=>field.key===view.group_by)?.label??view.group_by}`:''}</button>
    </>} secondaryBar={<>{viewTools}<div className="toolbar-actions">{permissions.includes('export')&&adapter.definition.capabilities.includes('csv')&&<button onClick={()=>exportData.mutate()} disabled={exportData.isPending}>Export CSV</button>}{permissions.includes('import')&&adapter.definition.capabilities.includes('csv')&&adapter.renderExchange&&<button onClick={()=>setExchange(true)}>Import CSV</button>}</div></>} notice={notice?<div className="notice" role="status">{notice}<button aria-label="Dismiss notification" onClick={()=>setNotice('')}>×</button></div>:undefined} footer={<><span>{records.data?`${records.data.total===0?0:offset+1}–${offset+records.data.items.length} of ${records.data.total}`:'No result loaded'} · Search/filter/sort are server-scoped{view.group_by?' · grouping organizes this loaded page':''}.</span><div><button disabled={offset===0||records.isFetching} onClick={()=>setOffset(Math.max(0,offset-50))}>Previous</button><button disabled={!records.data||offset+50>=records.data.total||records.isFetching} onClick={()=>setOffset(offset+50)}>Next</button></div></>}>
    {selection.length>0&&<div className="selection-action-bar" role="region" aria-label="Selected record actions"><div><strong>{selection.length}</strong><span> selected on this page</span></div><div className="toolbar-actions"><RecordActionMenu adapter={adapter} row={selection[0]!} selectionCount={selection.length} permissions={[...(canWrite?['write']:[]),...(canRestore?['restore']:[]),'read']} placement="selection" callbacks={{open:()=>openRow(selection[0]!),peek:()=>setPeek(selection[0]!),edit:canWrite&&selection.length===1?()=>setForm(selection[0]!):undefined,bulkEdit:canWrite&&!view.archived&&adapter.entityKey?()=>setBulkEdit(true):undefined,transition:action=>{bulk.reset();setConfirm(action)}}}/></div></div>}
    {adapter.previewMatching&&adapter.bulkMatching&&records.data&&records.data.total>records.data.items.length&&(!view.archived?canWrite:canRestore)&&<div className="matching-scope-bar" role="region" aria-label="All matching records"><span>{records.data.total.toLocaleString()} records match this server query; the current page contains {records.data.items.length}.</span><button onClick={()=>matchingPreview.mutate()} disabled={matchingPreview.isPending}>{matchingPreview.isPending?'Reviewing…':'Review all matching records'}</button></div>}
    {records.isError&&<ErrorNotice error={records.error} retry={()=>{void records.refetch()}}/>}
    {exportData.isError&&<ErrorNotice error={exportData.error}/>} {transition.isError&&<ErrorNotice error={transition.error}/>}
    {records.isPending?<div className="loading-state" role="status">Loading records…</div>:!records.isError&&records.data?.items.length===0?<EmptyState title="No matching records" description="Adjust the filters or create the first record. A failed request is never shown as an empty dataset."/>:!records.isError&&<DataGrid<T> rows={records.data?.items??[]} definition={adapter.definition} density={view.density??'comfortable'} columns={view.columns??[]} groupBy={view.group_by??''} scope={scope} onOpen={openRow} onPeek={setPeek} onHover={handleHover} onContext={(row,anchor)=>{setHover(null);setContext({row,anchor})}} onSelection={setSelection} onColumns={columns=>setView(current=>({...current,columns}))}/>}
    <RecordPeek adapter={adapter} row={peek} permissions={[...(canWrite?['write']:[]),...(canRestore?['restore']:[]),'read']} onClose={()=>setPeek(null)} onOpen={row=>{setPeek(null);openRow(row)}} onEdit={canWrite?row=>{setPeek(null);setForm(row)}:undefined}/>
    <HoverRecordPreview row={hover?.row??null} anchor={hover?.anchor??{x:0,y:0}} adapter={adapter} onClose={()=>setHover(null)}/>
    <TableContextMenu row={context?.row??null} anchor={context?.anchor??{x:0,y:0}} adapter={adapter} canWrite={canWrite} canRestore={canRestore} onClose={()=>setContext(null)} onOpen={openRow} onPeek={setPeek} onEdit={setForm} onTransition={(row,action)=>transition.mutate({row,action})} onCopyLink={row=>{void copyLink(row)}}/>
    <TableDisplayControls open={Boolean(displayAnchor)} anchor={displayAnchor??{x:0,y:0}} definition={adapter.definition} view={view} onChange={next=>setView(next)} onClose={()=>setDisplayAnchor(null)}/>
    {itemId&&detail.isError&&<Dialog title="Record unavailable" onClose={closeRow}><ErrorNotice error={detail.error}/></Dialog>}
    {detail.data&&itemId&&form===null&&<Dossier<T> adapter={adapter} api={api} row={detail.data} user={user} tenant={tenant} canWrite={canWrite} canRestore={canRestore} onClose={closeRow} onEdit={canWrite?()=>setForm(detail.data??null):undefined} onChanged={refresh}/>}
    {form!==null&&<RecordForm<T> adapter={adapter} row={form==='new'?undefined:form} onClose={()=>setForm(null)} onSaved={row=>{setForm(null);setNotice('Changes saved.');refresh();openRow(row)}}/>}
    {exchange&&adapter.renderExchange?.(()=>setExchange(false),()=>{setExchange(false);refresh();setNotice('Import completed.')})}
    {bulkEdit&&selection.length>0&&<BulkEditDialog api={api} adapter={adapter} rows={selection} onClose={()=>setBulkEdit(false)} onDone={count=>{setBulkEdit(false);setNotice(`${count} records updated atomically.`);refresh()}}/>}
    {matchingScope&&<Dialog title={`${matchingScope.view.archived?'Restore':'Archive'} all ${matchingScope.preview.total.toLocaleString()} matching records?`} onClose={()=>setMatchingScope(null)} busy={matchingApply.isPending} footer={<><button disabled={matchingApply.isPending} onClick={()=>setMatchingScope(null)}>Cancel</button><button className="danger" disabled={matchingApply.isPending} onClick={()=>matchingApply.mutate({scope:matchingScope,action:matchingScope.view.archived?'restore':'archive'})}>{matchingApply.isPending?'Applying…':'Confirm matching scope'}</button></>}><p>This operation re-evaluates the saved server query and applies only if its count and ID/revision fingerprint are unchanged. Hidden rows matching the query are intentionally included.</p><div className="bulk-preview-list" aria-label="Matching records preview">{matchingScope.preview.sample.map(row=><span key={row.id}>{String((row as unknown as Record<string,unknown>)[adapter.definition.primary_field]??row.id)}</span>)}{matchingScope.preview.total>matchingScope.preview.sample.length&&<span>+ {matchingScope.preview.total-matchingScope.preview.sample.length} more</span>}</div>{(matchingPreview.isError||matchingApply.isError)&&<ErrorNotice error={matchingPreview.error??matchingApply.error}/>}</Dialog>}
    {confirm&&<Dialog title={`${confirm==='archive'?'Archive':'Restore'} ${selection.length} selected records?`} onClose={()=>setConfirm(null)} busy={bulk.isPending} footer={<><button disabled={bulk.isPending} onClick={()=>setConfirm(null)}>Cancel</button><button className="danger" disabled={bulk.isPending} onClick={()=>bulk.mutate(confirm)}>{bulk.isPending?'Applying…':'Confirm change'}</button></>}><p>Only the explicit selection on this page is included. If any selected record has changed, no record in this batch is modified.</p><div className="bulk-preview-list" aria-label="Selected records preview">{selectedLabels.map(label=><span key={label}>{label}</span>)}{selection.length>selectedLabels.length&&<span>+ {selection.length-selectedLabels.length} more</span>}</div>{bulk.isError&&<ErrorNotice error={bulk.error}/>}</Dialog>}
  </WorkspaceShell>
}
