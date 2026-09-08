import { useMemo } from 'react'
import type { WorkspaceContext } from '../../platform/workspace/context'
import { EntityWorkspace } from '../../platform/workspace/EntityWorkspace'
import { adapter } from './adapter'
import { PlanningWorkspace } from '../../platform/workspace/PlanningWorkspace'
export function Workspace(props:WorkspaceContext){const value=useMemo(()=>adapter(props.api,props.definition),[props.api,props.definition]);return <EntityWorkspace {...props} adapter={value} visualizations={['planning','table','board','gantt','calendar','timeline','dashboard','graph']} customProjections={{planning:PlanningWorkspace}}/>}
