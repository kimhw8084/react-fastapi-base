import type { ViewDefinition, WorkspaceDefinition } from '../../generated/schema'
import { DEFAULT_VIEW } from './types'

export type WorkspaceVisualization = string
export const CURRENT_WORKSPACE_SCHEMA = 2

export function resolveWorkspaceVisualizations(definition: WorkspaceDefinition, requested?: readonly string[]): string[] {
  const declared = definition.visualizations?.length ? definition.visualizations : ['table']
  const wanted = requested?.length ? requested : declared
  const allowed = new Set(declared)
  const values = Array.from(new Set(wanted)).filter(value => allowed.has(value))
  return values.length ? values : [declared[0] ?? 'table']
}

export function sanitizeWorkspaceView(
  definition: WorkspaceDefinition,
  available: readonly string[],
  value: unknown,
  defaultDensity: 'comfortable' | 'compact' = 'comfortable',
): ViewDefinition {
  const source = value && typeof value === 'object' ? value as Partial<ViewDefinition> : {}
  const fields = new Map(definition.fields.map(field => [field.key, field]))
  const filters: Record<string, string> = {}
  if (source.filters && typeof source.filters === 'object') {
    for (const [key, selected] of Object.entries(source.filters)) {
      const field = fields.get(key)
      if (!definition.filter_keys.includes(key) || typeof selected !== 'string') continue
      if (field?.choices.length && !field.choices.includes(selected)) continue
      filters[key] = selected
    }
  }
  const seen = new Set<string>()
  const columns = Array.isArray(source.columns) ? source.columns.filter(column => {
    if (!column || typeof column.colId !== 'string' || !definition.columns.includes(column.colId) || seen.has(column.colId)) return false
    seen.add(column.colId)
    return true
  }).slice(0, 30) : []
  const sorts = Array.isArray(source.sorts) ? source.sorts.flatMap(item => {
    if (!item || typeof item !== 'object') return []
    const candidate = item as { key?: unknown; direction?: unknown }
    return typeof candidate.key === 'string' && definition.sort_keys.includes(candidate.key)
      ? [{ key: candidate.key, direction: candidate.direction === 'asc' ? 'asc' as const : 'desc' as const }]
      : []
  }).slice(0, 8) : []
  const advanced_filters = Array.isArray(source.advanced_filters) ? source.advanced_filters.flatMap(item => {
    if (!item || typeof item !== 'object') return []
    const candidate = item as Record<string, unknown>
    return typeof candidate.key === 'string' && definition.filter_keys.includes(candidate.key) && typeof candidate.value === 'string'
      ? [{ key: candidate.key, operator: typeof candidate.operator === 'string' ? candidate.operator.slice(0, 20) : 'eq', value: candidate.value.slice(0, 200) }]
      : []
  }).slice(0, 20) : []
  const fallbackVisualization = available[0] ?? definition.visualizations?.[0] ?? 'table'
  const visualization = typeof source.visualization === 'string' && available.includes(source.visualization)
    ? source.visualization
    : fallbackVisualization
  return {
    ...DEFAULT_VIEW,
    schema_version: CURRENT_WORKSPACE_SCHEMA,
    search: typeof source.search === 'string' ? source.search.slice(0, 200) : '',
    filters,
    advanced_filters,
    archived: source.archived === true,
    group_by: typeof source.group_by === 'string' && definition.filter_keys.includes(source.group_by) ? source.group_by : '',
    sort: typeof source.sort === 'string' && definition.sort_keys.includes(source.sort) ? source.sort : (definition.sort_keys.includes('updated_at') ? 'updated_at' : definition.sort_keys[0] ?? 'updated_at'),
    direction: source.direction === 'asc' ? 'asc' : 'desc',
    sorts,
    density: source.density === 'compact' ? 'compact' : source.density === 'comfortable' ? 'comfortable' : defaultDensity,
    visualization,
    columns,
  }
}

export function migrateWorkspaceView(definition: WorkspaceDefinition, available: readonly string[], value: unknown, defaultDensity: 'comfortable'|'compact' = 'comfortable'): ViewDefinition {
  const source = value && typeof value === 'object' ? {...value as Record<string, unknown>} : {}
  const legacySort = typeof source.sort === 'string' ? source.sort : 'updated_at'
  const legacyDirection = source.direction === 'asc' ? 'asc' : 'desc'
  if (!Array.isArray(source.sorts)) source.sorts = [{key: legacySort, direction: legacyDirection}]
  if (!Array.isArray(source.advanced_filters)) source.advanced_filters = []
  return sanitizeWorkspaceView(definition, available, source, defaultDensity)
}

export interface ViewReconciliation { view: ViewDefinition; conflict: boolean; winner: 'local'|'server'|'same' }

export function reconcileWorkspaceView(definition: WorkspaceDefinition, available: readonly string[], local: unknown, server: ViewDefinition|null, defaultDensity: 'comfortable'|'compact' = 'comfortable'): ViewReconciliation {
  const localView = migrateWorkspaceView(definition, available, local, defaultDensity)
  if (!server) return {view: localView, conflict: false, winner: 'local'}
  const serverView = migrateWorkspaceView(definition, available, server, defaultDensity)
  const localJson = JSON.stringify(localView), serverJson = JSON.stringify(serverView)
  if (localJson === serverJson) return {view: serverView, conflict: false, winner: 'same'}
  return {view: serverView, conflict: true, winner: 'server'}
}
