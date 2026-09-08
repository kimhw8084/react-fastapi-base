import type { ApiClient } from '../api/client'
import type { WorkspaceDefinition } from '../../generated/schema'
export interface WorkspaceContext {
  api: ApiClient
  definition: WorkspaceDefinition
  appId: string
  tenant: string
  user: string
  permissions: readonly string[]
  defaultDensity: 'comfortable' | 'compact'
}
