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
  const query:ListQuery = {
    search: view.search,
    filters: view.filters,
    archived: view.archived,
    sort: view.sort,
    direction: view.direction,
    limit,
    offset,
  }
  // Older generated adapters spread ListQuery into URLSearchParams. Keep rich
  // state available to upgraded adapters without leaking `[object Object]`
  // into legacy endpoints during the compatibility window.
  Object.defineProperties(query, {
    sorts: {value:view.sorts, enumerable:false},
    advanced_filters: {value:normalizeAdvancedFilters(view.advanced_filters), enumerable:false},
  })
  return query
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
