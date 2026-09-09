import type { ViewDefinition } from '../../generated/schema'
import type { WorkspaceContext } from './context'
import type { BaseRecord,WorkspaceAdapter } from './types'
import { ProjectionWorkspaceFrame } from './ProjectionWorkspaceFrame'
import { categoricalField,displayValue,primaryLabel,recordValue } from './projectionUtils'
import type { CSSProperties, ReactNode } from 'react'
import { useEffect,useState } from 'react'
import { readStorage,storageKey,writeStorage } from '../state/storage'
import { DEFAULT_DASHBOARD,applyDashboardVariables,dashboardForView,dashboardFromView,responsiveColumns,sanitizeDashboard,type DashboardLayout } from './dashboardModel'

interface Props<T extends BaseRecord> extends WorkspaceContext{adapter:WorkspaceAdapter<T>;view:ViewDefinition;onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void;searchInput:string;onSearchInput:(value:string)=>void;viewTools?:ReactNode}
export function DashboardWorkspace<T extends BaseRecord>(props:Props<T>){
 const category=categoricalField(props.adapter.definition);const field=props.adapter.definition.fields.find(value=>value.key===category)
 const layoutKey=storageKey(props.appId,props.user,props.tenant,`dashboard.${props.adapter.key}`,2)
 const [layout,setLayout]=useState<DashboardLayout>(()=>dashboardFromView(props.view.dashboard)??readStorage(layoutKey,DEFAULT_DASHBOARD,value=>sanitizeDashboard(value)))
 const [width,setWidth]=useState(()=>window.innerWidth)
 useEffect(()=>{const listener=()=>setWidth(window.innerWidth);window.addEventListener('resize',listener);return()=>window.removeEventListener('resize',listener)},[])
 useEffect(()=>{writeStorage(layoutKey,layout)},[layoutKey,layout])
 useEffect(()=>{
  const serverLayout=dashboardFromView(props.view.dashboard)
  if(serverLayout&&JSON.stringify(serverLayout)!==JSON.stringify(layout))setLayout(serverLayout)
 },[props.view.dashboard])
 useEffect(()=>{
  const serialized=JSON.stringify(dashboardForView(layout))
  if(JSON.stringify(props.view.dashboard)!==serialized)props.onViewChange(current=>({...current,dashboard:dashboardForView(layout)}))
 },[layout,props.onViewChange,props.view.dashboard])
 return <ProjectionWorkspaceFrame {...props} projectionKey="dashboard" title={`${props.adapter.definition.label} dashboard`} description="Configurable analytical projection built from the same workspace query. Metric drill-down opens the same records and dossier used by operational views.">{(rows,{openRow,peekRow})=>{
  const currentColumns=responsiveColumns(layout,width);const variableKeys=[...new Set(['timeRange','status','owner',category].filter((key):key is string=>key==='timeRange'||Boolean(key&&props.adapter.definition.fields.some(field=>field.key===key))))];const filtered=applyDashboardVariables(rows,layout.variables,(row,key)=>recordValue(row,key));
  const counts=new Map<string,number>();filtered.forEach(row=>{const value=category?displayValue(recordValue(row,category)):'All';counts.set(value,(counts.get(value)??0)+1)});const max=Math.max(1,...counts.values())
  const updateVariable=(key:string,value:string)=>setLayout(current=>({...current,variables:{...current.variables,[key]:value}}))
  const toggleWidget=(id:string)=>setLayout(current=>({...current,widgets:current.widgets.map(widget=>widget.id===id?{...widget,visible:!widget.visible}:widget)}))
  return <div className="dashboard-projection" style={{'--dashboard-columns':currentColumns} as CSSProperties}><header className="dashboard-composer-toolbar">{variableKeys.map(key=>{const label=key==='timeRange'?'Time range':props.adapter.definition.fields.find(item=>item.key===key)?.label??key.replaceAll('_',' ');const options=key==='timeRange'?['all','24h','7d','30d']:[...new Set(rows.map(row=>String(recordValue(row,key)??'')))].filter(Boolean);return <label key={key}>{label}<select value={layout.variables[key]??'all'} onChange={event=>updateVariable(key,event.target.value)}><option value="all">All</option>{options.filter(value=>value!=='all').map(value=><option key={value} value={value}>{value.replaceAll('_',' ')}</option>)}</select></label>})}<label>Columns<select value={layout.columns} onChange={event=>setLayout(current=>({...current,columns:Number(event.target.value) as DashboardLayout['columns']}))}><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option></select></label><div className="dashboard-widget-toggles">{layout.widgets.map(widget=><button key={widget.id} aria-pressed={widget.visible} onClick={()=>toggleWidget(widget.id)}>{widget.title}</button>)}</div></header><section className="dashboard-widget-grid">{layout.widgets.filter(widget=>widget.visible).map(widget=>widget.id==='metrics'?<section className="dashboard-metric-grid" key={widget.id}><article><span>Visible records</span><strong>{filtered.length}</strong></article><article><span>{field?.label??'Grouping'}</span><strong>{counts.size}</strong></article></section>:widget.id==='distribution'?<section className="dashboard-chart" key={widget.id} aria-label={`${field?.label??'Record'} distribution`}><h3>{field?.label??'Record'} distribution</h3>{[...counts.entries()].map(([label,count])=><button className="dashboard-bar" key={label} onClick={()=>updateVariable(category??'status',label)}><span>{label.replaceAll('_',' ')}</span><div><i style={{width:`${(count/max)*100}%`}}/></div><strong>{count}</strong></button>)}</section>:<section className="dashboard-recent" key={widget.id}><h3>{widget.title}</h3>{filtered.slice(0,8).map(row=><article key={row.id}><button onClick={()=>openRow(row)}>{primaryLabel(row,props.adapter.definition)}</button><button className="peek-button" onClick={()=>peekRow(row)}>Quick look</button></article>)}</section>)}</section></div>
 }}</ProjectionWorkspaceFrame>
}
