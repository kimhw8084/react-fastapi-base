import { useState,type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import type { RelationshipRead,ViewDefinition } from '../../generated/schema'
import type { WorkspaceContext } from './context'
import type { BaseRecord,WorkspaceAdapter } from './types'
import { ProjectionWorkspaceFrame } from './ProjectionWorkspaceFrame'
import { primaryLabel } from './projectionUtils'
import { ErrorNotice } from '../ui/Notice'

interface Props<T extends BaseRecord> extends WorkspaceContext{adapter:WorkspaceAdapter<T>;view:ViewDefinition;onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void;searchInput:string;onSearchInput:(value:string)=>void;viewTools?:ReactNode}
interface Node{key:string;entity:string;id:string;label:string;workspace:string;row?:BaseRecord;x:number;y:number}
export function GraphWorkspace<T extends BaseRecord>(props:Props<T>){
 const [trace,setTrace]=useState<string|null>(null)
 const relationships=useQuery({queryKey:['relationship-graph',props.user,props.tenant,props.adapter.entityKey??props.adapter.key,props.view.archived],queryFn:({signal})=>props.api.request<RelationshipRead[]>(`/api/v1/relationships/graph?${new URLSearchParams({entity:props.adapter.entityKey??props.adapter.key,include_archived:String(props.view.archived),limit:'500'})}`,{signal})})
 return <ProjectionWorkspaceFrame {...props} projectionKey="graph" title={`${props.adapter.definition.label} relationship graph`} description="Relationship-aware projection of canonical records. Trace mode emphasizes directly connected records without copying graph-specific data.">{(rows,{openRow,peekRow})=>{
  const currentEntity=props.adapter.entityKey??props.adapter.key
  const refs=new Map<string,{entity:string;id:string;label:string;workspace:string;row?:T}>()
  rows.forEach(row=>refs.set(`${currentEntity}:${row.id}`,{entity:currentEntity,id:row.id,label:primaryLabel(row,props.adapter.definition),workspace:props.adapter.key,row}))
  for(const relationship of relationships.data??[]){for(const ref of [relationship.source,relationship.target])refs.set(`${ref.entity}:${ref.id}`,{entity:ref.entity,id:ref.id,label:ref.label,workspace:ref.workspace,row:ref.entity===currentEntity?rows.find(row=>row.id===ref.id):undefined})}
  const ordered=[...refs.values()].sort((a,b)=>a.entity.localeCompare(b.entity)||a.label.localeCompare(b.label));const columns=Math.max(1,Math.min(4,Math.ceil(Math.sqrt(ordered.length))));const nodes:Node[]=ordered.map((node,index)=>({...node,key:`${node.entity}:${node.id}`,x:40+(index%columns)*240,y:40+Math.floor(index/columns)*150}));const byKey=new Map(nodes.map(node=>[node.key,node]));const traced=new Set<string>();if(trace){traced.add(trace);for(const rel of relationships.data??[]){const a=`${rel.source.entity}:${rel.source.id}`,b=`${rel.target.entity}:${rel.target.id}`;if(a===trace)traced.add(b);if(b===trace)traced.add(a)}}const width=Math.max(720,columns*240);const height=Math.max(360,Math.ceil(nodes.length/columns)*150+60)
  return <div className="graph-projection-wrap">{relationships.isError&&<ErrorNotice error={relationships.error}/>}<div className="graph-toolbar"><span>{relationships.data?.length??0} relationships</span>{trace&&<button onClick={()=>setTrace(null)}>Clear trace</button>}</div><div className="graph-projection" style={{width,height}} role="region" aria-label={`${props.adapter.definition.label} relationship graph`}><svg width={width} height={height} aria-hidden="true">{(relationships.data??[]).map(rel=>{const a=byKey.get(`${rel.source.entity}:${rel.source.id}`),b=byKey.get(`${rel.target.entity}:${rel.target.id}`);if(!a||!b)return null;const highlighted=!trace||trace===a.key||trace===b.key;return <line key={rel.id} x1={a.x+90} y1={a.y+45} x2={b.x+90} y2={b.y+45} className={highlighted?'graph-edge active':'graph-edge'}/>})}</svg>{nodes.map(node=>{const dimmed=trace&&!traced.has(node.key);return <article className={`graph-node${dimmed?' dimmed':''}`} style={{left:node.x,top:node.y}} key={node.key}><span>{node.entity.replaceAll('_',' ')}</span>{node.row?<button className="graph-node-title" onClick={()=>openRow(node.row as T)}>{node.label}</button>:<Link className="graph-node-title" to={`/${node.workspace.replaceAll('_','-')}?item=${encodeURIComponent(node.id)}`}>{node.label}</Link>}<div><button onClick={()=>setTrace(node.key)} aria-pressed={trace===node.key}>Trace</button>{node.row&&<button onClick={()=>peekRow(node.row as T)}>Peek</button>}</div></article>})}</div></div>
 }}</ProjectionWorkspaceFrame>
}
