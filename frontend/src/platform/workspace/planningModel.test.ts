import { describe, expect, it } from 'vitest'
import { baselineSlipDays, criticalPath } from './planningModel'

describe('planning schedule calculations', () => {
  it('calculates positive baseline slip and ignores early completion', () => {
    expect(baselineSlipDays('2026-03-10', '2026-03-07')).toBe(3)
    expect(baselineSlipDays('2026-03-07', '2026-03-10')).toBe(0)
    expect(baselineSlipDays('', '2026-03-10')).toBe(0)
  })

  it('keeps critical path dependency traversal deterministic', () => {
    expect(criticalPath([{ id: 'a', duration: 2 }, { id: 'b', duration: 5 }, { id: 'c', duration: 1 }], [{ source: 'b', target: 'a' }, { source: 'c', target: 'b' }])).toEqual(['a', 'b', 'c'])
  })
})
