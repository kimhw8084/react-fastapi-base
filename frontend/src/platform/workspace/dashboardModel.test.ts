import { describe, expect, it } from 'vitest'
import { dashboardForView, dashboardFromView, DEFAULT_DASHBOARD, responsiveColumns, sanitizeDashboard } from './dashboardModel'

describe('dashboard composer state', () => {
  it('sanitizes and round-trips the server snake-case layout contract', () => {
    const layout = sanitizeDashboard({
      schema_version: 2,
      columns: 4,
      variables: { timeRange: '7d', ignored: 'removed' },
      widgets: [{ id: 'health', kind: 'health', title: 'Health', span: 2, visible: true, filter_key: 'status' }],
    })
    expect(layout.columns).toBe(4)
    expect(layout.variables).toEqual({ timeRange: '7d' })
    expect(layout.widgets[0]).toMatchObject({ id: 'health', kind: 'health', filterKey: 'status' })
    expect(dashboardForView(layout)).toEqual({
      schema_version: 2,
      columns: 4,
      variables: { timeRange: '7d' },
      widgets: [{ id: 'health', kind: 'health', title: 'Health', span: 2, visible: true, filter_key: 'status' }],
    })
  })

  it('uses a bounded default for malformed or absent saved layouts', () => {
    expect(dashboardFromView(null)).toBeNull()
    expect(sanitizeDashboard({ columns: 99, widgets: [{ id: '', kind: 'unknown', title: 'unsafe' }] })).toEqual(DEFAULT_DASHBOARD)
  })

  it('reduces columns at mobile breakpoints without changing the saved layout', () => {
    expect(responsiveColumns({ ...DEFAULT_DASHBOARD, columns: 4 }, 420)).toBe(1)
    expect(responsiveColumns({ ...DEFAULT_DASHBOARD, columns: 4 }, 760)).toBe(2)
    expect(responsiveColumns({ ...DEFAULT_DASHBOARD, columns: 4 }, 1400)).toBe(4)
  })
})
