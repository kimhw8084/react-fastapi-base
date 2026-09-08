import { useMemo } from 'react'
import type { WorkspaceContext } from '../../platform/workspace/context'
import { EntityWorkspace } from '../../platform/workspace/EntityWorkspace'
import { workItemsAdapter } from './adapter'
export function Workspace(props: WorkspaceContext) {
  const {api,definition,user,tenant,permissions}=props
  const adapter=useMemo(()=>workItemsAdapter(api,definition,permissions.includes('write'),`${user}:${tenant}`),[api,definition,user,tenant,permissions])
  return <EntityWorkspace {...props} adapter={adapter} visualizations={['table','board','dashboard','timeline','calendar','gantt','graph']}/>
}
