import { useMemo } from 'react'
import type { WorkspaceContext } from '../../platform/workspace/context'
import { EntityWorkspace } from '../../platform/workspace/EntityWorkspace'
import { SpcWorkspace } from '../../platform/workspace/SpcWorkspace'
import { adapter } from './adapter'
export function Workspace(props:WorkspaceContext){const value=useMemo(()=>adapter(props.api,props.definition),[props.api,props.definition]);return <EntityWorkspace {...props} adapter={value} visualizations={['spc','table','timeline','dashboard']} customProjections={{spc:SpcWorkspace}}/>}
