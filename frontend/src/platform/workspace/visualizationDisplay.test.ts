import { describe, expect, it } from 'vitest'
import { visualizationDisplayLabel } from './visualizationDisplay'

const registeredVisualizationIds = [
  'board', 'calendar', 'dashboard', 'designer', 'gantt', 'graph', 'incident_command',
  'investigation', 'knowledge', 'observability', 'pipeline', 'planning', 'rack',
  'recipe', 'research', 'risk', 'slo', 'spc', 'state_timeline', 'table', 'timeline', 'traveler', 'wafer',
]

describe('shared visualization display labels', () => {
  it('humanizes every registered visualization ID without changing the stable key', () => {
    for (const key of registeredVisualizationIds) {
      const before = key
      const label = visualizationDisplayLabel(key)
      expect(label, key).not.toMatch(/[_-]/)
      expect(label, key).not.toBe(key)
      expect(key, 'display formatting must not mutate visualization state').toBe(before)
    }
  })

  it('uses deliberate labels for named IDs and sensible labels for custom compound IDs', () => {
    expect(visualizationDisplayLabel('state_timeline')).toBe('State timeline')
    expect(visualizationDisplayLabel('incident_command')).toBe('Incident command')
    expect(visualizationDisplayLabel('spc')).toBe('SPC')
    expect(visualizationDisplayLabel('slo')).toBe('SLO')
    expect(visualizationDisplayLabel('gantt')).toBe('Gantt')
    expect(visualizationDisplayLabel('custom_projection_v2')).toBe('Custom projection v2')
    expect(visualizationDisplayLabel('custom-projection-v2')).toBe('Custom projection v2')
  })

  it('rejects the raw underscore label as a negative control', () => {
    const key = 'state_timeline'
    const rawLabel = key[0]!.toUpperCase() + key.slice(1)
    expect(rawLabel).toContain('_')
    expect(rawLabel).not.toBe(visualizationDisplayLabel(key))
  })
})
