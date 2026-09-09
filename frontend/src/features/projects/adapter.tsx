import type { AuditRead, ProjectCreate, ProjectPage, ProjectRead, WorkspaceDefinition } from '../../generated/schema'
import type { ApiClient } from '../../platform/api/client'
import { serializeListQuery } from '../../platform/workspace/query'
import type { Draft, WorkspaceAdapter } from '../../platform/workspace/types'

function parseDraft(draft:Draft):ProjectCreate{
  const status=draft.status
  if(status!=='planned'&&status!=='active'&&status!=='blocked'&&status!=='complete')throw new Error('Choose a valid project status.')
  return {title:draft.title??'',summary:draft.summary??'',status,owner:draft.owner??''}
}
export function projectsAdapter(api:ApiClient,definition:WorkspaceDefinition):WorkspaceAdapter<ProjectRead>{
 const base='/api/v1/projects'
 return {
  key:'projects',entityKey:'projects',singular:'project',definition,
  list:(query,signal)=>api.request<ProjectPage>(`${base}?${serializeListQuery(query)}`,{signal}),
  get:id=>api.request<ProjectRead>(`${base}/${encodeURIComponent(id)}`),
  create:(draft,key)=>api.json<ProjectRead>(base,'POST',parseDraft(draft),key),
  update:(row,draft)=>api.json<ProjectRead>(`${base}/${row.id}`,'PUT',{...parseDraft(draft),revision:row.revision}),
  transition:(row,action)=>api.json<ProjectRead>(`${base}/${row.id}/lifecycle/${action}`,'POST',{revision:row.revision}),
  bulk:(rows,action,key)=>api.json<ProjectRead[]>(`${base}/bulk`,'POST',{action,targets:rows.map(row=>({id:row.id,revision:row.revision}))},key),
  history:id=>api.request<AuditRead[]>(`${base}/${encodeURIComponent(id)}/history`),
  revert:(row,target)=>api.json<ProjectRead>(`${base}/${row.id}/revert`,'POST',{revision:row.revision,target_revision:target}),
  draft:row=>({title:row?.title??'',summary:row?.summary??'',status:row?.status??'planned',owner:row?.owner??''}),
  export:async()=>{throw new Error('Project export is not enabled until schema-versioned exchange is implemented.')},
 }
}
