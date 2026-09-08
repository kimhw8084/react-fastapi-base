import { useEffect, useMemo, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import type { ColDef, ColumnState, GridApi, GridReadyEvent } from 'ag-grid-community'
import type { ViewColumn, WorkspaceDefinition } from '../../generated/schema'
import type { BaseRecord } from '../workspace/types'
import { groupRows, materializeColumns, visibleColumnIds } from '../workspace/tableModel'

ModuleRegistry.registerModules([AllCommunityModule])

export interface GridAnchor { x:number; y:number }
interface Props<T extends BaseRecord> {
  rows:T[]; definition:WorkspaceDefinition; density:'comfortable'|'compact'
  columns:ViewColumn[]; scope:string; groupBy?:string; onOpen:(row:T)=>void; onPeek?:(row:T)=>void
  onHover?:(row:T,anchor:GridAnchor|null)=>void; onContext?:(row:T,anchor:GridAnchor)=>void
  onSelection:(rows:T[])=>void; onColumns:(columns:ViewColumn[])=>void
}

function identityLabel<T extends BaseRecord>(row:T,definition:WorkspaceDefinition){return String(row[definition.primary_field as keyof T]??row.id)}
function hoverAnchor(event:React.MouseEvent<HTMLElement>):GridAnchor{const rect=event.currentTarget.getBoundingClientRect();return{x:Math.min(window.innerWidth-20,rect.right+8),y:Math.max(12,rect.top)}}

function GroupedSemanticGrid<T extends BaseRecord>({rows,definition,density,columns,scope,groupBy,onOpen,onPeek,onHover,onContext,onSelection}:Props<T>&{groupBy:string}){
 const [selected,setSelected]=useState<Set<string>>(new Set())
 const [collapsed,setCollapsed]=useState<Set<string>>(new Set())
 useEffect(()=>{setSelected(new Set());onSelection([])},[scope,onSelection])
 const groups=useMemo(()=>groupRows(rows,groupBy),[rows,groupBy])
 const visible=useMemo(()=>visibleColumnIds(definition,columns),[definition,columns])
 const state=useMemo(()=>new Map(materializeColumns(definition,columns).map(column=>[column.colId,column])),[definition,columns])
 const emit=(ids:Set<string>)=>{setSelected(new Set(ids));onSelection(rows.filter(row=>ids.has(row.id)))}
 const toggleRow=(row:T,checked:boolean)=>{const next=new Set(selected);checked?next.add(row.id):next.delete(row.id);emit(next)}
 const toggleGroup=(groupRows:T[],checked:boolean)=>{const next=new Set(selected);for(const row of groupRows){checked?next.add(row.id):next.delete(row.id)}emit(next)}
 const fieldLabel=(key:string)=>definition.fields.find(field=>field.key===key)?.label??key.replaceAll('_',' ')
 return <div className={`grouped-data-grid ${density}`} aria-label={`${definition.label} grouped by ${fieldLabel(groupBy)}`}>
  {groups.map(group=>{const isCollapsed=collapsed.has(group.key);const selectedCount=group.rows.filter(row=>selected.has(row.id)).length;return <section className="grouped-table-section" key={group.key}>
   <header className="grouped-table-header">
    <button className="group-toggle" aria-expanded={!isCollapsed} onClick={()=>setCollapsed(current=>{const next=new Set(current);next.has(group.key)?next.delete(group.key):next.add(group.key);return next})}>{isCollapsed?'▸':'▾'} <strong>{group.label}</strong> <span>{group.rows.length}</span></button>
    <label><input type="checkbox" aria-label={`Select all ${group.label}`} checked={selectedCount===group.rows.length&&group.rows.length>0} ref={node=>{if(node)node.indeterminate=selectedCount>0&&selectedCount<group.rows.length}} onChange={event=>toggleGroup(group.rows,event.target.checked)}/> {selectedCount?`${selectedCount} selected`:'Select group'}</label>
   </header>
   {!isCollapsed&&<div className="grouped-table-scroll"><table><thead><tr><th className="selection-cell">Select</th>{visible.map(key=><th key={key} style={{width:state.get(key)?.width}}>{fieldLabel(key)}</th>)}<th className="row-utility">Quick</th></tr></thead><tbody>{group.rows.map(row=><tr key={row.id} className={selected.has(row.id)?'selected':''} onDoubleClick={()=>onOpen(row)} onContextMenu={event=>{event.preventDefault();onContext?.(row,{x:event.clientX,y:event.clientY})}}>
    <td className="selection-cell"><input type="checkbox" aria-label={`Select ${identityLabel(row,definition)}`} checked={selected.has(row.id)} onChange={event=>toggleRow(row,event.target.checked)}/></td>
    {visible.map(key=><td key={key}>{key===definition.primary_field?<button className="cell-link" onMouseEnter={event=>onHover?.(row,hoverAnchor(event))} onMouseLeave={()=>onHover?.(row,null)} onClick={()=>onOpen(row)}>{identityLabel(row,definition)}</button>:String(row[key as keyof T]??'')}</td>)}
    <td className="row-utility">{onPeek&&<button className="peek-button" onClick={()=>onPeek(row)} aria-label={`Quick look ${identityLabel(row,definition)}`}>◫</button>}</td>
   </tr>)}</tbody></table></div>}
  </section>})}
 </div>
}

export function DataGrid<T extends BaseRecord>(props:Props<T>){
 const {rows,definition,density,columns,scope,groupBy='',onOpen,onPeek,onHover,onContext,onSelection,onColumns}=props
 if(groupBy)return <GroupedSemanticGrid {...props} groupBy={groupBy}/>
 return <StandardDataGrid rows={rows} definition={definition} density={density} columns={columns} scope={scope} onOpen={onOpen} onPeek={onPeek} onHover={onHover} onContext={onContext} onSelection={onSelection} onColumns={onColumns}/>
}

function StandardDataGrid<T extends BaseRecord>({rows,definition,density,columns,scope,onOpen,onPeek,onHover,onContext,onSelection,onColumns}:Props<T>){
  const grid=useRef<AgGridReact<T>>(null)
  const applied=useRef('')
  const apiRef=useRef<GridApi<T>|null>(null)
  const defs=useMemo<ColDef<T>[]>(()=>[
    ...definition.columns.map((key):ColDef<T>=>({
      colId:key,headerName:definition.fields.find(field=>field.key===key)?.label??key.replaceAll('_',' '),
      valueGetter:params=>params.data?String(params.data[key as keyof T]??''):'',
      minWidth:key===definition.primary_field?240:110,width:key===definition.primary_field?320:160,
      resizable:true,sortable:true,
      ...(key===definition.primary_field?{cellRenderer:(params:{data?:T})=>params.data?<div className="cell-identity-actions" onMouseEnter={event=>{if(params.data)onHover?.(params.data,hoverAnchor(event))}} onMouseLeave={()=>{if(params.data)onHover?.(params.data,null)}}><button className="cell-link" onClick={event=>{event.stopPropagation();if(params.data)onOpen(params.data)}}>{identityLabel(params.data,definition)}</button>{onPeek&&<button className="peek-button" title="Quick look" aria-label={`Quick look ${identityLabel(params.data,definition)}`} onClick={event=>{event.stopPropagation();if(params.data)onPeek(params.data)}}>◫</button>}</div>:null}:{}),
    })),
  ],[definition,onOpen,onPeek,onHover])
  const apply=(api:GridApi<T>)=>{
    const serialized=JSON.stringify(columns)
    if(applied.current!==serialized){applied.current=serialized;if(columns.length)api.applyColumnState({state:columns as ColumnState[],applyOrder:true});else api.resetColumnState()}
  }
  useEffect(()=>{if(apiRef.current)apply(apiRef.current)},[columns])
  useEffect(()=>{grid.current?.api?.deselectAll();onSelection([])},[scope,onSelection])
  const changed=()=>{
    const api=apiRef.current;if(!api)return
    const state:ViewColumn[]=api.getColumnState().filter(column=>definition.columns.includes(column.colId)).map(column=>({colId:column.colId,width:Math.max(60,Math.min(1200,Math.round(column.width??160))),hide:Boolean(column.hide),sort:column.sort??null,sortIndex:column.sortIndex??null,pinned:column.pinned==='left'||column.pinned==='right'?column.pinned:null}))
    const serialized=JSON.stringify(state);if(applied.current!==serialized){applied.current=serialized;onColumns(state)}
  }
  const ready=(event:GridReadyEvent<T>)=>{apiRef.current=event.api;apply(event.api)}
  return <div className="ag-theme-alpine golden-grid" aria-label={`${definition.label} data grid`}>
    <AgGridReact<T> ref={grid} rowData={rows} columnDefs={defs} getRowId={params=>params.data.id}
      theme="legacy" rowSelection={{mode:'multiRow',enableClickSelection:false}} selectionColumnDef={{width:64,pinned:'left',resizable:false,headerName:'Select'}} animateRows={false}
      rowHeight={density==='compact'?40:52} headerHeight={44} suppressContextMenu
      onGridReady={ready} onSelectionChanged={event=>onSelection(event.api.getSelectedRows())}
      onRowDoubleClicked={event=>{if(event.data)onOpen(event.data)}}
      onCellContextMenu={event=>{const native=event.event as MouseEvent;if(event.data&&native){native.preventDefault();onContext?.(event.data,{x:native.clientX,y:native.clientY})}}}
      onColumnResized={event=>{if(event.finished&&event.source==='uiColumnResized')changed()}}
      onColumnMoved={event=>{if(event.finished)changed()}} onColumnVisible={changed} onColumnPinned={changed} onSortChanged={changed}
      suppressCellFocus={false} overlayNoRowsTemplate="No records in this result." />
  </div>
}
