import { describe, expect, it } from 'vitest'
import { serializeListQuery, viewToListQuery } from './query'
import { DEFAULT_VIEW } from './types'

describe('workspace query contract', () => {
  it('encodes rich state without object stringification', () => {
    const query = viewToListQuery({
      ...DEFAULT_VIEW,
      filters: { status: 'active' },
      sorts: [{ key: 'priority', direction: 'desc' }],
      advanced_filters: [{ key: 'owner', operator: 'contains', value: 'kim' }],
    })
    const params = new URLSearchParams(serializeListQuery(query))
    expect(params.get('status')).toBe('active')
    expect(params.get('sorts')).toContain('priority')
    expect(params.get('advanced_filters')).toContain('contains')
    expect(params.toString()).not.toContain('%5Bobject+Object%5D')
  })
})
