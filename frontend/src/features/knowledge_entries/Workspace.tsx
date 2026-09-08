import { useMemo } from 'react'
import type { WorkspaceContext } from '../../platform/workspace/context'
import { EntityWorkspace } from '../../platform/workspace/EntityWorkspace'
import { adapter } from './adapter'
import { KnowledgeWorkspace } from '../../platform/workspace/KnowledgeWorkspace'
export function Workspace(props:WorkspaceContext){const value=useMemo(()=>adapter(props.api,props.definition),[props.api,props.definition]);return <EntityWorkspace {...props} adapter={value} visualizations={['knowledge', 'table', 'timeline', 'dashboard', 'graph']} customProjections={{knowledge:KnowledgeWorkspace}}/>}
