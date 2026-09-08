import type { ViewDefinition } from '../../generated/schema'
import type { WorkspaceContext } from './context'
import type { BaseRecord,WorkspaceAdapter } from './types'
import { ProjectionWorkspaceFrame } from './ProjectionWorkspaceFrame'
import { chooseEndField,chooseStartField,primaryLabel,recordDate } from './projectionUtils'
import type { ReactNode } from 'react'

interface Props<T extends BaseRecord> extends WorkspaceContext{adapter:WorkspaceAdapter<T>;view:ViewDefinition;onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void;searchInput:string;onSearchInput:(value:string)=>void;viewTools?:ReactNode}
export function GanttWorkspace<T extends BaseRecord>(props:Props<T>){
 const startField=chooseStartField(props.adapter.definition);const endField=chooseEndField(props.adapter.definition,startField)
 return <ProjectionWorkspaceFrame {...props} projectionKey="gantt" title={`${props.adapter.definition.label} Gantt`} description={`Schedule projection using ${startField.replaceAll('_',' ')} → ${endField.replaceAll('_',' ')}. Records remain canonical; this view does not create a separate task store.`}>{(rows,{openRow,peekRow})=>{
  const items=rows.map(row=>{const start=recordDate(row,startField);const end=recordDate(row,endField)??start;return {row,start,end:end&&start&&end<start?start:end}}).filter(item=>item.start&&item.end) as Array<{row:T;start:Date;end:Date}>
  const min=Math.min(...items.map(item=>item.start.getTime()));const max=Math.max(...items.map(item=>item.end.getTime()),min+86400000);const span=Math.max(1,max-min)
  return <div className="gantt-projection" role="table" aria-label={`${props.adapter.definition.label} Gantt`}><div className="gantt-scale" aria-hidden="true"><span>{Number.isFinite(min)?new Date(min).toLocaleDateString():'—'}</span><span>{Number.isFinite(max)?new Date(max).toLocaleDateString():'—'}</span></div>{items.map(({row,start,end})=>{const left=((start.getTime()-min)/span)*100;const width=Math.max(1.5,((end.getTime()-start.getTime())/span)*100);return <div className="gantt-row" role="row" key={row.id}><button role="rowheader" onClick={()=>openRow(row)}>{primaryLabel(row,props.adapter.definition)}</button><div className="gantt-track" role="cell"><button className="gantt-bar" style={{left:`${left}%`,width:`${Math.min(100-left,width)}%`}} onClick={()=>peekRow(row)} aria-label={`Quick look ${primaryLabel(row,props.adapter.definition)} from ${start.toLocaleDateString()} to ${end.toLocaleDateString()}`}/></div></div>})}</div>
 }}</ProjectionWorkspaceFrame>
}
