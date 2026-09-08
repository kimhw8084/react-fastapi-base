import type { ViewDefinition } from '../../generated/schema'
import type { WorkspaceContext } from './context'
import type { BaseRecord,WorkspaceAdapter } from './types'
import { ProjectionWorkspaceFrame } from './ProjectionWorkspaceFrame'
import { chooseStartField,primaryLabel,recordDate } from './projectionUtils'
import type { ReactNode } from 'react'

interface Props<T extends BaseRecord> extends WorkspaceContext{adapter:WorkspaceAdapter<T>;view:ViewDefinition;onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void;searchInput:string;onSearchInput:(value:string)=>void;viewTools?:ReactNode}
export function CalendarWorkspace<T extends BaseRecord>(props:Props<T>){
 const dateField=chooseStartField(props.adapter.definition)
 return <ProjectionWorkspaceFrame {...props} projectionKey="calendar" title={`${props.adapter.definition.label} calendar`} description="Month-oriented projection of the same canonical records. Shared filters and saved views remain authoritative when switching back to another visualization.">{(rows,{openRow,peekRow})=>{
  const groups=new Map<string,{date:Date;rows:T[]}>()
  rows.forEach(row=>{const date=recordDate(row,dateField);if(!date)return;const key=`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}`;const group=groups.get(key)??{date:new Date(date.getFullYear(),date.getMonth(),1),rows:[]};group.rows.push(row);groups.set(key,group)})
  const months=[...groups.values()].sort((a,b)=>a.date.getTime()-b.date.getTime())
  return <div className="calendar-projection" role="list" aria-label={`${props.adapter.definition.label} calendar`}>{months.map(month=><section key={month.date.toISOString()} className="calendar-month" role="listitem"><header><h3>{new Intl.DateTimeFormat(undefined,{month:'long',year:'numeric'}).format(month.date)}</h3><span>{month.rows.length} records</span></header><div className="calendar-events">{month.rows.sort((a,b)=>(recordDate(a,dateField)?.getTime()??0)-(recordDate(b,dateField)?.getTime()??0)).map(row=><article key={row.id}><time>{recordDate(row,dateField)?new Intl.DateTimeFormat(undefined,{day:'numeric',month:'short'}).format(recordDate(row,dateField)!):'—'}</time><button onClick={()=>openRow(row)}>{primaryLabel(row,props.adapter.definition)}</button><button className="peek-button" onClick={()=>peekRow(row)}>◫</button></article>)}</div></section>)}</div>
 }}</ProjectionWorkspaceFrame>
}
