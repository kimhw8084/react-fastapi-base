import type { WorkspaceDefinition } from '../../generated/schema'
import { fieldDisplayText, fieldPresentation } from '../../platform/workspace/FieldValue'

const severityLabels: Record<string, string> = {
  sev_1: 'SEV-1',
  sev_2: 'SEV-2',
  sev_3: 'SEV-3',
  sev_4: 'SEV-4',
}

export function incidentSeverityLabel(key: string): string {
  return severityLabels[key] ?? fieldDisplayText({ kind: 'select', precision: null, unit: null }, key)
}

export function incidentFieldLabel(definition: WorkspaceDefinition, key: string, value: unknown): string {
  return fieldDisplayText(fieldPresentation(definition, key), value)
}

export function incidentPresentation(definition: WorkspaceDefinition, record: object) {
  const values = record as Record<string, unknown>
  const severityKey = String(values.severity ?? '')
  return {
    severityKey,
    severityLabel: incidentSeverityLabel(severityKey),
    statusLabel: incidentFieldLabel(definition, 'status', values.status),
    startedAtLabel: incidentFieldLabel(definition, 'started_at', values.started_at),
    resolvedAtLabel: incidentFieldLabel(definition, 'resolved_at', values.resolved_at),
  }
}
