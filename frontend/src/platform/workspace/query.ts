import type { ViewDefinition } from '../../generated/schema'
import type { ListQuery } from './types'

/**
 * Encode the platform query contract once. Adapters must not stringify rich
 * workspace state as `[object Object]` or accidentally send presentation-only
 * fields to an endpoint.
 */
export function serializeListQuery(query: ListQuery): string {
  const params = new URLSearchParams()
  params.set('search', query.search)
  params.set('archived', String(query.archived))
  params.set('sort', query.sort)
  params.set('direction', query.direction)
  params.set('limit', String(query.limit))
  params.set('offset', String(query.offset))
  for (const [key, value] of Object.entries(query.filters)) {
    if (value) params.set(key, value)
  }
  if (query.sorts?.length) params.set('sorts', JSON.stringify(query.sorts))
  if (query.advanced_filters?.length) params.set('advanced_filters', JSON.stringify(query.advanced_filters))
  return params.toString()
}

export function viewToListQuery(view: ViewDefinition, offset = 0, limit = 50): ListQuery {
  return {
    search: view.search,
    filters: view.filters,
    archived: view.archived,
    sort: view.sort,
    direction: view.direction,
    sorts: view.sorts,
    advanced_filters: normalizeAdvancedFilters(view.advanced_filters),
    limit,
    offset,
  }
}

export function normalizeAdvancedFilters(value: unknown): Array<{key:string;operator:string;value:string}> {
  if (!Array.isArray(value)) return []
  return value.flatMap(item => {
    if (!item || typeof item !== 'object') return []
    const candidate = item as Record<string, unknown>
    return typeof candidate.key === 'string' && typeof candidate.value === 'string'
      ? [{key:candidate.key, operator:typeof candidate.operator === 'string' ? candidate.operator : 'eq', value:candidate.value}]
      : []
  })
}
