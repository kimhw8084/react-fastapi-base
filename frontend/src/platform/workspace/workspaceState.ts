import type { ViewDefinition, WorkspaceDefinition } from '../../generated/schema'
import { DEFAULT_VIEW } from './types'

export type WorkspaceVisualization = string

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
  const fallbackVisualization = available[0] ?? definition.visualizations?.[0] ?? 'table'
  const visualization = typeof source.visualization === 'string' && available.includes(source.visualization)
    ? source.visualization
    : fallbackVisualization
  return {
    ...DEFAULT_VIEW,
    search: typeof source.search === 'string' ? source.search.slice(0, 200) : '',
    filters,
    archived: source.archived === true,
    group_by: typeof source.group_by === 'string' && definition.filter_keys.includes(source.group_by) ? source.group_by : '',
    sort: typeof source.sort === 'string' && definition.sort_keys.includes(source.sort) ? source.sort : (definition.sort_keys.includes('updated_at') ? 'updated_at' : definition.sort_keys[0] ?? 'updated_at'),
    direction: source.direction === 'asc' ? 'asc' : 'desc',
    density: source.density === 'compact' ? 'compact' : source.density === 'comfortable' ? 'comfortable' : defaultDensity,
    visualization,
    columns,
  }
}
