import type { WorkspaceDefinition } from '../../generated/schema'
import { fieldDisplayText, fieldPresentation } from '../../platform/workspace/FieldValue'

export function equipmentStateFieldLabel(definition: WorkspaceDefinition, key: string, value: unknown): string {
  return fieldDisplayText(fieldPresentation(definition, key), value)
}

export function equipmentStatePresentation(definition: WorkspaceDefinition, record: object) {
  const values = record as Record<string, unknown>
  return {
    stateKey: String(values.state ?? ''),
    stateLabel: equipmentStateFieldLabel(definition, 'state', values.state),
    startedAtLabel: equipmentStateFieldLabel(definition, 'started_at', values.started_at),
    endedAtLabel: equipmentStateFieldLabel(definition, 'ended_at', values.ended_at),
  }
}
