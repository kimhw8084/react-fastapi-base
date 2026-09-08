import type { WorkItemCreate, WorkItemPage, WorkItemRead, AuditRead, WorkspaceDefinition } from '../../generated/schema'
import type { ApiClient } from '../../platform/api/client'
import type { Draft, WorkspaceAdapter } from '../../platform/workspace/types'
import { Attachments } from './Attachments'
import { Exchange } from './Exchange'

function parseDraft(draft:Draft):WorkItemCreate{
 const status=draft.status;const priority=draft.priority
 if(status!=='open'&&status!=='in_progress'&&status!=='done')throw new Error('Choose a valid status.')
 if(priority!=='low'&&priority!=='normal'&&priority!=='high')throw new Error('Choose a valid priority.')
 return {title:draft.title??'',description:draft.description??'',status,priority}
}
export function workItemsAdapter(api:ApiClient,definition:WorkspaceDefinition,canWrite:boolean,scope:string):WorkspaceAdapter<WorkItemRead>{
 const base='/api/v1/work-items'
 return {
  key:'work_items',entityKey:'work_items',singular:'work item',definition,
  list:(query,signal)=>api.request<WorkItemPage>(`${base}?${new URLSearchParams(Object.entries({...query,...query.filters,filters:undefined}).filter(([,value])=>value!==undefined).map(([k,v])=>[k,String(v)]))}`,{signal}),
  get:id=>api.request<WorkItemRead>(`${base}/${encodeURIComponent(id)}`),
  create:(draft,key)=>api.json<WorkItemRead>(base,'POST',parseDraft(draft),key),
  update:(row,draft)=>api.json<WorkItemRead>(`${base}/${row.id}`,'PUT',{...parseDraft(draft),revision:row.revision}),
  transition:(row,action)=>api.json<WorkItemRead>(`${base}/${row.id}/lifecycle/${action}`,'POST',{revision:row.revision}),
  bulk:(rows,action,key)=>api.json<WorkItemRead[]>(`${base}/bulk`,'POST',{action,targets:rows.map(row=>({id:row.id,revision:row.revision}))},key),
  history:id=>api.request<AuditRead[]>(`${base}/${id}/history`),
  revert:(row,target)=>api.json<WorkItemRead>(`${base}/${row.id}/revert`,'POST',{revision:row.revision,target_revision:target}),
  draft:row=>({title:row?.title??'',description:row?.description??'',status:row?.status??'open',priority:row?.priority??'normal'}),
  renderAttachments:row=><Attachments api={api} itemId={row.id} canWrite={canWrite&&!row.archived} scope={scope}/>,
  renderExchange:(onClose,onDone)=><Exchange api={api} onClose={onClose} onDone={onDone}/>,
  export:query=>api.download(`${base}/export.csv?${new URLSearchParams({search:query.search,status:query.filters.status??'',priority:query.filters.priority??'',archived:String(query.archived)})}`,'work-items-v1.csv'),
 }
}
