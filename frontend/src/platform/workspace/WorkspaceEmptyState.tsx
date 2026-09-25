import { EmptyState } from '../ui/Notice'
import type { ViewDefinition } from '../../generated/schema'

interface Props {
 label:string
 singular:string
 view:ViewDefinition
 searchInput:string
 canWrite:boolean
 onViewChange:(value:ViewDefinition|((current:ViewDefinition)=>ViewDefinition))=>void
 onSearchInput:(value:string)=>void
 onCreate?:()=>void
}

export function WorkspaceEmptyState({label,singular,view,searchInput,canWrite,onViewChange,onSearchInput,onCreate}:Props){
 const searched=Boolean(searchInput.trim()||view.search.trim())
 const filtered=Object.values(view.filters).some(Boolean)||Boolean(view.advanced_filters?.length)
 const noMatch=searched||filtered
 const clear=()=>{
  onSearchInput('')
  onViewChange(current=>({...current,search:'',filters:{},advanced_filters:[]}))
 }
 if(noMatch)return <EmptyState title={`No matching ${label.toLocaleLowerCase()}`} description={`No ${view.archived?'archived':'active'} ${label.toLocaleLowerCase()} match the current search or filters.`} actions={<button type="button" onClick={clear}>Clear search and filters</button>}/>
 if(view.archived)return <EmptyState title={`No archived ${label.toLocaleLowerCase()}`} description={`Archived ${label.toLocaleLowerCase()} will appear here after they are archived.`} actions={<button type="button" onClick={()=>onViewChange(current=>({...current,archived:false}))}>Show active records</button>}/>
 return <EmptyState title={`No active ${label.toLocaleLowerCase()} yet`} description={`Create the first ${singular} to begin using this workspace.`} actions={canWrite&&onCreate?<button type="button" className="primary" onClick={onCreate}>Create first {singular}</button>:undefined}/>
}
