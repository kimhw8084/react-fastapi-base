import { useMemo } from 'react'
import type { WorkspaceContext } from '../../platform/workspace/context'
import { EntityWorkspace } from '../../platform/workspace/EntityWorkspace'
import { projectsAdapter } from './adapter'
export function Workspace(props:WorkspaceContext){
 const adapter=useMemo(()=>projectsAdapter(props.api,props.definition),[props.api,props.definition])
 return <EntityWorkspace {...props} adapter={adapter} visualizations={['table','board','dashboard','timeline','calendar','gantt','graph']}/>
}
