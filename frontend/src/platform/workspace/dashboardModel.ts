export type DashboardWidgetKind='metric'|'chart'|'table'|'timeline'|'health'|'alert'|'markdown'
export interface DashboardWidget { id:string; kind:DashboardWidgetKind; title:string; span:1|2|3|4; visible:boolean; filterKey?:string }
export interface DashboardLayout { schemaVersion:2; columns:1|2|3|4; widgets:DashboardWidget[]; variables:Record<string,string> }
export const DEFAULT_DASHBOARD:DashboardLayout={schemaVersion:2,columns:3,variables:{timeRange:'all',status:'all',owner:'all'},widgets:[
 {id:'metrics',kind:'metric',title:'Key metrics',span:3,visible:true},
 {id:'distribution',kind:'chart',title:'Distribution',span:2,visible:true},
 {id:'records',kind:'table',title:'Records',span:1,visible:true},
]}
export function sanitizeDashboard(value:unknown):DashboardLayout{
 const source=value&&typeof value==='object'?value as Partial<DashboardLayout>:{}
 const columns=source.columns===1||source.columns===2||source.columns===4?source.columns:3
 const candidateVariables=source.variables&&typeof source.variables==='object'?Object.fromEntries(Object.entries(source.variables).filter(([key,item])=>['timeRange','status','owner','category'].includes(key)&&typeof item==='string').map(([key,item])=>[key,String(item).slice(0,80)])):{}
 const variables=Object.keys(candidateVariables).length?candidateVariables:{...DEFAULT_DASHBOARD.variables}
 const widgets=Array.isArray(source.widgets)?source.widgets.flatMap(raw=>{if(!raw||typeof raw!=='object')return[];const item=raw as Partial<DashboardWidget>&{filter_key?:unknown};if(typeof item.id!=='string'||typeof item.title!=='string'||!['metric','chart','table','timeline','health','alert','markdown'].includes(String(item.kind)))return[];const span=item.span===1||item.span===2||item.span===4?item.span:3;const filterKey=typeof item.filterKey==='string'?item.filterKey:typeof item.filter_key==='string'?item.filter_key:undefined;return[{id:item.id.slice(0,60),kind:item.kind as DashboardWidgetKind,title:item.title.slice(0,120),span,visible:item.visible!==false,filterKey}] as DashboardWidget[]}):[]
 return {schemaVersion:2,columns,variables,widgets:widgets.length?widgets:DEFAULT_DASHBOARD.widgets.map(widget=>({...widget})),}
}
export function dashboardFromView(value:unknown):DashboardLayout|null{
 if(value===null||value===undefined)return null
 return sanitizeDashboard(value)
}
export function dashboardForView(layout:DashboardLayout){
 return {schema_version:2,columns:layout.columns,variables:layout.variables,widgets:layout.widgets.map(widget=>({id:widget.id,kind:widget.kind,title:widget.title,span:widget.span,visible:widget.visible,filter_key:widget.filterKey??null}))}
}
export function responsiveColumns(layout:DashboardLayout,width:number):1|2|3|4{if(width<620)return 1;if(width<980)return Math.min(2,layout.columns) as 1|2;if(width<1280)return Math.min(3,layout.columns) as 1|2|3;return layout.columns}
export function crossFilter<T>(rows:readonly T[],key:string,value:string,get:(row:T,key:string)=>unknown):T[]{if(!value||value==='all')return[...rows];return rows.filter(row=>String(get(row,key)??'')===value)}
export function applyDashboardVariables<T>(rows:readonly T[],variables:Record<string,string>,get:(row:T,key:string)=>unknown,now=Date.now()):T[]{
 return rows.filter(row=>Object.entries(variables).every(([key,value])=>{
  if(!value||value==='all')return true
  if(key==='timeRange'){
   const timestamp=Date.parse(String(get(row,'updated_at')??''));
   const days=value==='24h'?1:value==='7d'?7:value==='30d'?30:0
   return !days||!Number.isFinite(timestamp)||timestamp>=now-days*86400000
  }
  return String(get(row,key)??'')===value
 }))
}
