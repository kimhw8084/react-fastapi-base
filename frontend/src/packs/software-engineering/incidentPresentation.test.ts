import { describe, expect, it } from 'vitest'
import type { FieldDefinition, WorkspaceDefinition } from '../../generated/schema'
import { incidentPresentation } from './incidentPresentation'

const field = (key: string, kind: FieldDefinition['kind'], choices: string[] = []): FieldDefinition => ({
  key, label: key, kind, choices, required: false, nullable: true, max_length: null, minimum: null, maximum: null,
  step: null, unit: null, precision: null, display_format: null, searchable: true, filterable: true, sortable: true,
  exportable: true, computed: false, read_only: false,
})

describe('Incident Command presentation', () => {
  it('displays severity, enum status and timestamps without changing canonical data', () => {
    const definition = { fields: [
      field('severity', 'select', ['sev_1', 'sev_2', 'sev_3', 'sev_4']),
      field('status', 'select', ['in_progress', 'resolved']),
      field('started_at', 'datetime'),
      field('resolved_at', 'datetime'),
    ] } as WorkspaceDefinition
    const record = Object.freeze({
      severity: 'sev_2', status: 'in_progress', started_at: '2025-04-17T08:30:00.000Z', resolved_at: null,
    })

    expect(incidentPresentation(definition, record)).toEqual({
      severityKey: 'sev_2', severityLabel: 'SEV-2', statusLabel: 'In Progress',
      startedAtLabel: expect.stringMatching(/2025|Apr|17/), resolvedAtLabel: '—',
    })
    expect(record).toEqual({ severity: 'sev_2', status: 'in_progress', started_at: '2025-04-17T08:30:00.000Z', resolved_at: null })
  })

  it('covers every supported severity label while preserving the canonical class key', () => {
    const definition = { fields: [field('severity', 'select')] } as WorkspaceDefinition
    for (const [key, label] of [['sev_1', 'SEV-1'], ['sev_2', 'SEV-2'], ['sev_3', 'SEV-3'], ['sev_4', 'SEV-4']]) {
      const presentation = incidentPresentation(definition, { severity: key })
      expect(presentation.severityKey).toBe(key)
      expect(presentation.severityLabel).toBe(label)
    }
  })
})
