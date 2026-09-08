import type { ViewDefinition } from '../../generated/schema'
import type { WorkspaceContext } from './context'
import type { BaseRecord,WorkspaceAdapter } from './types'
import { ProjectionWorkspaceFrame } from './ProjectionWorkspaceFrame'
import { categoricalField,displayValue,primaryLabel,recordValue } from './projectionUtils'
import type { ReactNode } from 'react'

interface Props<T extends BaseRecord> extends WorkspaceContext{adapter:WorkspaceAdapter<T>;view:ViewDefinition;onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void;searchInput:string;onSearchInput:(value:string)=>void;viewTools?:ReactNode}
export function DashboardWorkspace<T extends BaseRecord>(props:Props<T>){
 const category=categoricalField(props.adapter.definition);const field=props.adapter.definition.fields.find(value=>value.key===category)
 return <ProjectionWorkspaceFrame {...props} projectionKey="dashboard" title={`${props.adapter.definition.label} dashboard`} description="Configurable analytical projection built from the same workspace query. Metric drill-down opens the same records and dossier used by operational views.">{(rows,{openRow,peekRow})=>{
  const counts=new Map<string,number>();rows.forEach(row=>{const value=category?displayValue(recordValue(row,category)):'All';counts.set(value,(counts.get(value)??0)+1)});const max=Math.max(1,...counts.values())
  return <div className="dashboard-projection"><section className="dashboard-metric-grid"><article><span>Visible records</span><strong>{rows.length}</strong></article><article><span>{field?.label??'Grouping'}</span><strong>{counts.size}</strong></article></section><section className="dashboard-chart" aria-label={`${field?.label??'Record'} distribution`}><h3>{field?.label??'Record'} distribution</h3>{[...counts.entries()].map(([label,count])=><div className="dashboard-bar" key={label}><span>{label.replaceAll('_',' ')}</span><div><i style={{width:`${(count/max)*100}%`}}/></div><strong>{count}</strong></div>)}</section><section className="dashboard-recent"><h3>Records</h3>{rows.slice(0,8).map(row=><article key={row.id}><button onClick={()=>openRow(row)}>{primaryLabel(row,props.adapter.definition)}</button><button className="peek-button" onClick={()=>peekRow(row)}>Quick look</button></article>)}</section></div>
 }}</ProjectionWorkspaceFrame>
}
