import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import type { EntityReference, RelationshipDefinition, RelationshipRead } from '../../generated/schema'
import type { ApiClient } from '../api/client'
import { ErrorNotice, EmptyState } from '../ui/Notice'

interface Props {
  api: ApiClient
  entity: string
  recordId: string
  user: string
  tenant: string
  canWrite: boolean
  readOnly?: boolean
}

function counterpart(relationship:RelationshipRead,entity:string,recordId:string):EntityReference{
  return relationship.source.entity===entity&&relationship.source.id===recordId?relationship.target:relationship.source
}

export function Relationships({api,entity,recordId,user,tenant,canWrite,readOnly=false}:Props){
  const client=useQueryClient()
  const [definitionKey,setDefinitionKey]=useState('')
  const [query,setQuery]=useState('')
  const [selected,setSelected]=useState<EntityReference|null>(null)
  const definitions=useQuery({queryKey:['relationship-definitions',user,tenant],queryFn:()=>api.request<RelationshipDefinition[]>('/api/v1/relationships/definitions')})
  const relationships=useQuery({queryKey:['relationships',user,tenant,entity,recordId],queryFn:()=>api.request<RelationshipRead[]>(`/api/v1/relationships?${new URLSearchParams({entity,record_id:recordId})}`)})
  const applicable=useMemo(()=>definitions.data?.filter(value=>value.source_entity===entity||value.target_entity===entity)??[],[definitions.data,entity])
  const chosen=applicable.find(value=>value.key===definitionKey)??applicable[0]
  const otherEntity=chosen?(chosen.source_entity===entity?chosen.target_entity:chosen.source_entity):''
  const candidates=useQuery({
    queryKey:['entity-search',user,tenant,otherEntity,query],
    queryFn:()=>api.request<EntityReference[]>(`/api/v1/entities/${encodeURIComponent(otherEntity)}/search?${new URLSearchParams({q:query,limit:'20'})}`),
    enabled:Boolean(otherEntity)&&canWrite&&!readOnly,
  })
  const refresh=()=>{void client.invalidateQueries({queryKey:['relationships',user,tenant,entity,recordId]})}
  const create=useMutation({mutationFn:()=>{
    if(!chosen||!selected)throw new Error('Choose a relationship type and related record.')
    const sourceId=chosen.source_entity===entity?recordId:selected.id
    const targetId=chosen.target_entity===entity?recordId:selected.id
    return api.json<RelationshipRead>('/api/v1/relationships','POST',{definition_key:chosen.key,source_id:sourceId,target_id:targetId,metadata:{}})
  },onSuccess:()=>{setSelected(null);setQuery('');refresh()}})
  const archive=useMutation({mutationFn:(row:RelationshipRead)=>api.json<RelationshipRead>(`/api/v1/relationships/${encodeURIComponent(row.id)}/lifecycle/archive`,'POST',{revision:row.revision}),onSuccess:refresh})
  const activeDefinitions=new Map((definitions.data??[]).map(value=>[value.key,value]))
  return <section className="relationship-workspace" aria-label="Related records">
    {(definitions.isError||relationships.isError||create.isError||archive.isError)&&<ErrorNotice error={definitions.error??relationships.error??create.error??archive.error}/>} 
    {relationships.isPending?<p role="status">Loading relationships…</p>:relationships.data?.length?<div className="relationship-list">{relationships.data.map(row=>{
      const other=counterpart(row,entity,recordId);const definition=activeDefinitions.get(row.definition_key)
      const label=row.source.entity===entity?definition?.forward_label:definition?.reverse_label
      return <article key={row.id} className="relationship-card"><div><span className="eyebrow">{label??definition?.label??row.definition_key}</span><Link to={`/${other.workspace.replaceAll('_','-')}?item=${encodeURIComponent(other.id)}`}>{other.label}</Link><small>{other.entity.replaceAll('_',' ')}{other.archived?' · archived':''}</small></div>{canWrite&&!readOnly&&<button className="danger" disabled={archive.isPending} onClick={()=>archive.mutate(row)}>Unlink</button>}</article>
    })}</div>:!relationships.isPending&&<EmptyState title="No related records" description="Typed relationships keep canonical records connected without copying their data."/>}
    {canWrite&&!readOnly&&applicable.length>0&&<form className="relationship-linker" onSubmit={event=>{event.preventDefault();if(selected)create.mutate()}}>
      <h3>Link related record</h3>
      <div className="relationship-linker-grid">
        <label>Relationship<select value={chosen?.key??''} onChange={event=>{setDefinitionKey(event.target.value);setSelected(null);setQuery('')}}>{applicable.map(value=><option key={value.key} value={value.key}>{value.label}</option>)}</select></label>
        <label>Search {otherEntity.replaceAll('_',' ')}<input value={query} onChange={event=>{setQuery(event.target.value);setSelected(null)}} placeholder="Search canonical records…"/></label>
      </div>
      {candidates.isFetching&&<p className="muted" role="status">Searching…</p>}
      {candidates.isError&&<ErrorNotice error={candidates.error}/>} 
      {candidates.data&&<div className="relationship-candidates" role="listbox" aria-label="Related record candidates">{candidates.data.filter(row=>!(row.entity===entity&&row.id===recordId)).map(row=><button type="button" key={row.id} role="option" aria-selected={selected?.id===row.id} onClick={()=>setSelected(row)}><strong>{row.label}</strong><span>{row.archived?'Archived':'Active'} · revision {row.revision??'—'}</span></button>)}</div>}
      <div className="relationship-linker-actions"><span className="muted">{selected?`Selected: ${selected.label}`:'Choose one canonical record.'}</span><button className="primary" disabled={!selected||create.isPending} type="submit">{create.isPending?'Linking…':'Link record'}</button></div>
    </form>}
  </section>
}

export function RelationshipBadge({relationship, label}:{relationship:RelationshipRead;label?:string}){
  return <span className="relationship-badge" title={`${relationship.source.label} → ${relationship.target.label}`}>{label??relationship.definition_key.replaceAll('_',' ')}</span>
}

export function RelationshipPreview({relationship}:{relationship:RelationshipRead}){
  return <article className="relationship-preview"><RelationshipBadge relationship={relationship}/><strong>{relationship.source.label}</strong><span aria-hidden="true">→</span><strong>{relationship.target.label}</strong><small>Revision {relationship.revision}{relationship.archived?' · Archived':''}</small></article>
}

export function RelationshipTable({rows}:{rows:RelationshipRead[]}){
  return <div className="relationship-table" role="table" aria-label="Relationships">{rows.map(row=><RelationshipPreview key={row.id} relationship={row}/>)}</div>
}

export function RelationshipPicker({candidates,value,onChange,label='Related record'}:{candidates:EntityReference[];value:EntityReference|null;onChange:(value:EntityReference)=>void;label?:string}){
  return <div className="relationship-picker"><label>{label}<select value={value?.id??''} onChange={event=>{const next=candidates.find(candidate=>candidate.id===event.target.value);if(next)onChange(next)}}><option value="">Choose a canonical record…</option>{candidates.map(candidate=><option key={`${candidate.entity}:${candidate.id}`} value={candidate.id}>{candidate.label} · {candidate.entity.replaceAll('_',' ')}</option>)}</select></label></div>
}

type ExplorerProps=Pick<Props,'api'|'entity'|'recordId'|'user'|'tenant'>
function Explorer({api,entity,recordId,user,tenant,filter,title}:{api:ApiClient;entity:string;recordId:string;user:string;tenant:string;filter:(definition?:RelationshipDefinition)=>boolean;title:string}){
  const definitions=useQuery({queryKey:['relationship-definitions',user,tenant],queryFn:()=>api.request<RelationshipDefinition[]>('/api/v1/relationships/definitions')})
  const relationships=useQuery({queryKey:['relationships',user,tenant,entity,recordId],queryFn:()=>api.request<RelationshipRead[]>(`/api/v1/relationships?${new URLSearchParams({entity,record_id:recordId})}`)})
  const allowed=new Set((definitions.data??[]).filter(filter).map(definition=>definition.key))
  const rows=(relationships.data??[]).filter(row=>allowed.has(row.definition_key))
  return <section className="relationship-explorer" aria-label={title}><header><h3>{title}</h3><span>{rows.length}</span></header>{relationships.isPending?<p role="status">Loading relationships…</p>:rows.length?<RelationshipTable rows={rows}/>:<EmptyState title={`No ${title.toLowerCase()}`} description="The explorer reflects canonical typed relationships only."/>}</section>
}

export function RelatedRecords(props:ExplorerProps){return <Explorer {...props} filter={()=>true} title="Related records"/>}
export function BacklinkPanel(props:ExplorerProps){return <Explorer {...props} filter={definition=>Boolean(definition)} title="Backlinks"/>}
export function DependencyExplorer(props:ExplorerProps){return <Explorer {...props} filter={definition=>definition?.kind==='dependency'} title="Dependencies"/>}
export function ImpactExplorer(props:ExplorerProps){return <Explorer {...props} filter={definition=>definition?.kind==='dependency'} title="Impact"/>}
export function ConnectionExplorer(props:ExplorerProps){return <Explorer {...props} filter={definition=>definition?.kind==='connection'} title="Connections"/>}
export const RelationshipPanel=Relationships
export const RelationshipGraph=RelatedRecords

function NamedExplorer({api,entity,recordId,user,tenant,name,title}:{api:ApiClient;entity:string;recordId:string;user:string;tenant:string;name:string;title:string}){
 const query=useQuery({queryKey:['relationship-explorer',user,tenant,name,entity,recordId],queryFn:()=>api.request<RelationshipRead[]>(`/api/v1/relationships/${name}/explore?${new URLSearchParams({entity,record_id:recordId})}`)})
 return <section className="relationship-explorer" aria-label={title}><header><h3>{title}</h3><span>{query.data?.length??0}</span></header>{query.isPending?<p role="status">Loading {title.toLowerCase()}…</p>:query.isError?<ErrorNotice error={query.error}/>:query.data?.length?<RelationshipTable rows={query.data}/>:<EmptyState title={`No ${title.toLowerCase()}`} description="The explorer reflects canonical typed relationships only."/>}</section>
}

export function RelatedRecordsExplorer(props:ExplorerProps){return <NamedExplorer {...props} name="related" title="Related records"/>}
export function BacklinksExplorer(props:ExplorerProps){return <NamedExplorer {...props} name="backlinks" title="Backlinks"/>}
export function DependencyExplorerPanel(props:ExplorerProps){return <NamedExplorer {...props} name="dependencies" title="Dependencies"/>}
export function ImpactExplorerPanel(props:ExplorerProps){return <NamedExplorer {...props} name="impact" title="Impact"/>}
export function ConnectionExplorerPanel(props:ExplorerProps){return <NamedExplorer {...props} name="connections" title="Connections"/>}
