import type { ViewDefinition } from '../../generated/schema'
import type { WorkspaceContext } from './context'
import type { BaseRecord,WorkspaceAdapter } from './types'
import { ProjectionWorkspaceFrame } from './ProjectionWorkspaceFrame'
import { chooseStartField,displayValue,primaryLabel,recordDate,recordValue } from './projectionUtils'
import type { ReactNode } from 'react'

interface Props<T extends BaseRecord> extends WorkspaceContext{adapter:WorkspaceAdapter<T>;view:ViewDefinition;onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void;searchInput:string;onSearchInput:(value:string)=>void;viewTools?:ReactNode}
export function TimelineWorkspace<T extends BaseRecord>(props:Props<T>){
 const dateField=chooseStartField(props.adapter.definition)
 const fieldLabel=props.adapter.definition.fields.find(field=>field.key===dateField)?.label??(dateField==='created_at'?'Created':'Updated')
 return <ProjectionWorkspaceFrame {...props} projectionKey="timeline" title={`${props.adapter.definition.label} timeline`} description={`Chronological projection of canonical records using ${fieldLabel.toLowerCase()}. Opening an item keeps the shared dossier, relationships and history contract.`}>{(rows,{openRow,peekRow})=>{
  const ordered=[...rows].map(row=>({row,date:recordDate(row,dateField)})).sort((a,b)=>(b.date?.getTime()??0)-(a.date?.getTime()??0))
  return <ol className="entity-timeline" aria-label={`${props.adapter.definition.label} timeline`}>{ordered.map(({row,date})=><li key={row.id}><time>{date?new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:dateField==='created_at'||dateField==='updated_at'?'short':undefined}).format(date):'No date'}</time><div className="timeline-node" aria-hidden="true"/><article><button className="timeline-title" onClick={()=>openRow(row)}>{primaryLabel(row,props.adapter.definition)}</button><p>{props.adapter.definition.filter_keys.slice(0,2).map(key=>`${props.adapter.definition.fields.find(field=>field.key===key)?.label??key}: ${displayValue(recordValue(row,key))}`).join(' · ')}</p><button className="peek-button" onClick={()=>peekRow(row)}>Quick look</button></article></li>)}</ol>
 }}</ProjectionWorkspaceFrame>
}
