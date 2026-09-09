import type { ReactNode } from 'react'
import type { WorkspaceContext } from './context'
import type { AuditRead, MatchingBulkPreview, WorkspaceDefinition, ViewDefinition } from '../../generated/schema'
export interface BaseRecord { id: string; revision: number; archived: boolean }
export type Draft = Record<string, string>
export interface ListQuery {
  search: string
  filters: Record<string,string>
  archived: boolean
  sort: string
  direction: 'asc' | 'desc'
  sorts?: Array<{key:string;direction:'asc'|'desc'}>
  advanced_filters?: Array<{key:string;operator:string;value:string}>
  limit: number
  offset: number
}
export interface Page<T> { items: T[]; total: number; limit: number; offset: number }
export interface WorkspaceAdapter<T extends BaseRecord> {
  key: string
  entityKey?: string
  singular: string
  definition: WorkspaceDefinition
  list(query: ListQuery, signal?: AbortSignal): Promise<Page<T>>
  get(id: string): Promise<T>
  create(draft: Draft, key: string): Promise<T>
  update(row: T, draft: Draft): Promise<T>
  transition(row: T, action: 'archive' | 'restore'): Promise<T>
  bulk(rows: T[], action: 'archive' | 'restore', key: string): Promise<T[]>
  previewMatching?(view: ViewDefinition): Promise<MatchingBulkPreview>
  bulkMatching?(view: ViewDefinition, action: 'archive' | 'restore', expectedTotal: number, fingerprint: string, key: string): Promise<T[]>
  history(id: string): Promise<AuditRead[]>
  revert(row: T, revision: number): Promise<T>
  draft(row?: T): Draft
  renderDetails?: (row: T) => ReactNode
  renderAttachments?: (row: T) => ReactNode
  renderDossierTab?: (tab:'activity'|'comments'|'files'|'audit'|'actions', row:T) => ReactNode
  renderForm?: (draft: Draft, onChange: (draft: Draft) => void) => ReactNode
  renderExchange?: (onClose: () => void, onDone: () => void) => ReactNode
  export(query: ListQuery): Promise<void>
}

export interface ProjectionProps<T extends BaseRecord> extends WorkspaceContext {
  adapter: WorkspaceAdapter<T>
  view: ViewDefinition
  onViewChange: (value: ViewDefinition | ((current: ViewDefinition) => ViewDefinition)) => void
  searchInput: string
  onSearchInput: (value: string) => void
  viewTools?: ReactNode
}

export const DEFAULT_VIEW: ViewDefinition = { schema_version: 2, search: '', filters: {}, advanced_filters: [], archived: false, group_by: '', sort: 'updated_at', direction: 'desc', sorts: [], density: 'comfortable', visualization: 'table', columns: [], dashboard: null }
