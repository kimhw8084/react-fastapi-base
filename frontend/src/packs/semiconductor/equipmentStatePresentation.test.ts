import { describe, expect, it } from 'vitest'
import type { FieldDefinition, WorkspaceDefinition } from '../../generated/schema'
import { equipmentStatePresentation } from './equipmentStatePresentation'

const field = (key: string, kind: FieldDefinition['kind'], choices: string[] = []): FieldDefinition => ({
  key, label: key, kind, choices, required: false, nullable: true, max_length: null, minimum: null, maximum: null,
  step: null, unit: null, precision: null, display_format: null, searchable: true, filterable: true, sortable: true,
  exportable: true, computed: false, read_only: false,
})

describe('Equipment State presentation', () => {
  it('humanizes state and timestamp display while preserving canonical values', () => {
    const definition = { fields: [field('state', 'select', ['unscheduled_down']), field('started_at', 'datetime'), field('ended_at', 'datetime')] } as WorkspaceDefinition
    const record = Object.freeze({ state: 'unscheduled_down', started_at: '2025-04-17T08:30:00.000Z', ended_at: '2025-04-17T10:00:00.000Z' })
    const presentation = equipmentStatePresentation(definition, record)

    expect(presentation.stateKey).toBe('unscheduled_down')
    expect(presentation.stateLabel).toBe('Unscheduled Down')
    expect(presentation.startedAtLabel).not.toContain('T')
    expect(presentation.endedAtLabel).not.toContain('T')
    expect(record).toEqual({ state: 'unscheduled_down', started_at: '2025-04-17T08:30:00.000Z', ended_at: '2025-04-17T10:00:00.000Z' })
  })
})
