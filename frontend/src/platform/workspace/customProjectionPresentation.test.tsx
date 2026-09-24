import { describe, expect, it, vi } from 'vitest'

const { projectionRows } = vi.hoisted(() => ({ projectionRows: [] as Record<string, unknown>[] }))

vi.mock('./ProjectionWorkspaceFrame', () => ({
  ProjectionWorkspaceFrame: ({ children }: { children: (rows: Record<string, unknown>[], actions: Record<string, () => void>) => unknown }) =>
    children(projectionRows, { openRow: () => undefined, peekRow: () => undefined, refresh: () => undefined }),
}))

import { render } from '@testing-library/react'
import type { FieldDefinition, WorkspaceDefinition } from '../../generated/schema'
import type { BaseRecord, ProjectionProps } from './types'
import { EquipmentStateWorkspace } from '../../packs/semiconductor/EquipmentStateWorkspace'
import { LotTravelerWorkspace } from '../../packs/semiconductor/LotTravelerWorkspace'
import { RecipeWorkspace } from '../../packs/semiconductor/RecipeWorkspace'
import { WaferWorkspace } from '../../packs/semiconductor/WaferWorkspace'
import { DeliveryWorkspace } from '../../packs/software-engineering/DeliveryWorkspace'
import { IncidentWorkspace } from '../../packs/software-engineering/IncidentWorkspace'
import { ObservabilityWorkspace } from '../../packs/software-engineering/ObservabilityWorkspace'
import { SloWorkspace } from '../../packs/software-engineering/SloWorkspace'

const field = (key: string, kind: FieldDefinition['kind'], choices: string[] = [], extra: Partial<FieldDefinition> = {}): FieldDefinition => ({
  key, label: key.replaceAll('_', ' '), kind, required: false, nullable: true, max_length: null, choices,
  minimum: null, maximum: null, step: null, unit: null, precision: null, display_format: null,
  searchable: true, filterable: true, sortable: true, exportable: true, computed: false, read_only: false, ...extra,
})

function props(fields: FieldDefinition[]): ProjectionProps<BaseRecord> {
  return { adapter: { key: 'fixture', definition: { fields } as WorkspaceDefinition } } as unknown as ProjectionProps<BaseRecord>
}

function renderRows(row: Record<string, unknown>) {
  projectionRows.splice(0, projectionRows.length, row)
}

describe('custom projection field display', () => {
  it('formats governed values across all eight families and preserves canonical data and technical keys', () => {
    const timestamp = '2026-09-22T07:30:00Z'

    const equipmentRow = Object.freeze({ id: 'equipment-1', label: 'Pressure bridge', state: 'unscheduled_down', started_at: timestamp, ended_at: null, duration_minutes: 90, module: 'TMP-04', reason: 'Sensor quality alarm', alarm_code: 'SYN-PRESS-17' })
    renderRows(equipmentRow)
    const equipment = render(<EquipmentStateWorkspace {...props([field('label', 'text'), field('state', 'select'), field('started_at', 'datetime'), field('ended_at', 'datetime'), field('duration_minutes', 'duration', [])])} />)
    expect(equipment.container.querySelector('.state-utilization')).toHaveTextContent('Unscheduled Down')
    expect(equipment.container.querySelector('.state-workbench')).not.toHaveTextContent('unscheduled_down')
    expect(equipment.container.querySelector('.state-timeline-list')).not.toHaveTextContent(timestamp)
    expect(equipmentRow).toMatchObject({ state: 'unscheduled_down', started_at: timestamp })
    equipment.unmount()

    const lotRow = Object.freeze({ id: 'lot-1', lot_id: 'LOT-SYN-204', product: 'NX-14 sensor wafer', status: 'hold', priority: 'hot', quantity: 24, started_at: timestamp, target_complete: '2026-09-25T18:00:00Z', current_step: 'metrology_review', route: { steps: [{ id: 'step-1', name: 'Metrology review', status: 'hold' }] }, owner: 'demo.quality' })
    renderRows(lotRow)
    const lot = render(<LotTravelerWorkspace {...props([field('lot_id', 'text'), field('product', 'text'), field('status', 'select'), field('priority', 'select'), field('quantity', 'integer'), field('started_at', 'datetime'), field('target_complete', 'datetime'), field('current_step', 'text'), field('route', 'json'), field('owner', 'text')])} />)
    expect(lot.container.querySelector('.lot-list')).toHaveTextContent('Hold · Hot')
    expect(lot.container.querySelector('.lot-context')).toHaveTextContent('Hold')
    expect(lot.container.querySelector('.lot-context')).not.toHaveTextContent(timestamp)
    expect(lot.container.querySelector('.lot-route')).toHaveTextContent('hold')
    expect(lotRow).toMatchObject({ status: 'hold', priority: 'hot', started_at: timestamp, current_step: 'metrology_review' })
    lot.unmount()

    const recipeRow = Object.freeze({ id: 'recipe-1', name: 'Uniformity recovery', version_name: '2.4.1', process: 'deposition', status: 'released', parameters: { pressure_mTorr: 41.2 }, limits: { pressure_mTorr: [40, 42] } })
    renderRows(recipeRow)
    const recipe = render(<RecipeWorkspace {...props([field('name', 'text'), field('version_name', 'text'), field('process', 'text'), field('status', 'select'), field('parameters', 'json'), field('limits', 'json')])} />)
    expect(recipe.container.querySelector('.recipe-list')).toHaveTextContent('Released')
    expect(recipe.container.querySelector('.recipe-list')).not.toHaveTextContent('released')
    expect(recipe.container.querySelector('.recipe-list')).toHaveTextContent('2.4.1')
    expect(recipeRow).toMatchObject({ status: 'released', version_name: '2.4.1', parameters: { pressure_mTorr: 41.2 } })
    recipe.unmount()

    const waferRow = Object.freeze({ id: 'wafer-1', wafer_id: 'WFR-SYN-204-03', lot_id: 'LOT-SYN-204', process_step: 'metrology_review', status: 'hold', die_rows: 1, die_cols: 1, bin_map: { good_bins: ['PASS'], cells: [{ x: 0, y: 0, bin: 'PASS' }] }, yield_percent: 100, total_die: 1, good_die: 1, defect_count: 0 })
    renderRows(waferRow)
    const wafer = render(<WaferWorkspace {...props([field('wafer_id', 'text'), field('lot_id', 'text'), field('process_step', 'text'), field('status', 'select'), field('die_rows', 'integer'), field('die_cols', 'integer'), field('bin_map', 'json')])} />)
    expect(wafer.container.querySelector('.wafer-summary')).toHaveTextContent('Hold')
    expect(wafer.container.querySelector('.wafer-main header')).toHaveTextContent('metrology_review')
    expect(waferRow).toMatchObject({ status: 'hold', process_step: 'metrology_review', wafer_id: 'WFR-SYN-204-03' })
    wafer.unmount()

    const deliveryRow = Object.freeze({ id: 'delivery-1', run_id: 'deploy-syn-2041', status: 'failed', environment: 'test', commit_sha: '7f5e11a1d28c', branch: 'feature/spc-recovery', duration_minutes: 13, stages: {}, artifacts: {} })
    renderRows(deliveryRow)
    const delivery = render(<DeliveryWorkspace {...props([field('run_id', 'text'), field('status', 'select'), field('environment', 'select'), field('commit_sha', 'text'), field('branch', 'text'), field('duration_minutes', 'duration', [], { unit: 'min' })])} />)
    expect(delivery.container.querySelector('.delivery-list')).toHaveTextContent('Test')
    expect(delivery.container.querySelector('.delivery-list')).toHaveTextContent('Failed')
    expect(delivery.container.querySelector('.delivery-main')).toHaveTextContent('13 min')
    expect(delivery.container.querySelector('.delivery-main')).toHaveTextContent('7f5e11a1d28c')
    expect(deliveryRow).toMatchObject({ status: 'failed', environment: 'test', commit_sha: '7f5e11a1d28c', branch: 'feature/spc-recovery' })
    delivery.unmount()

    const incidentRow = Object.freeze({ id: 'incident-1', incident_number: 'INC-SYN-204', title: 'Pressure bridge drift', status: 'monitoring', severity: 'sev_2', started_at: timestamp, resolved_at: null, duration_minutes: 103, timeline: { events: [] }, actions: {} })
    renderRows(incidentRow)
    const incident = render(<IncidentWorkspace {...props([field('incident_number', 'text'), field('title', 'text'), field('status', 'select'), field('severity', 'select'), field('started_at', 'datetime'), field('resolved_at', 'datetime'), field('duration_minutes', 'duration'), field('timeline', 'json'), field('actions', 'json')])} />)
    expect(incident.container.querySelector('.incident-list')).toHaveTextContent('SEV-2')
    expect(incident.container.querySelector('.incident-context')).toHaveTextContent('Monitoring')
    expect(incident.container.querySelector('.incident-context')).not.toHaveTextContent(timestamp)
    expect(incidentRow).toMatchObject({ status: 'monitoring', severity: 'sev_2', started_at: timestamp })
    incident.unmount()

    const eventRow = Object.freeze({ id: 'event-1', event_id: 'evt-syn-5001', signal: 'metric', severity: 'warning', timestamp, duration_ms: 820.4, trace_id: 'trace-syn-09ab', span_id: 'span-syn-a100', operation: 'telemetry.ingest', message: 'Synthetic latency threshold crossed', attributes: {} })
    renderRows(eventRow)
    const observability = render(<ObservabilityWorkspace {...props([field('event_id', 'text'), field('signal', 'select'), field('severity', 'select'), field('timestamp', 'datetime'), field('duration_ms', 'number'), field('trace_id', 'text'), field('span_id', 'text'), field('operation', 'text'), field('message', 'textarea'), field('attributes', 'json')])} />)
    expect(observability.container.querySelector('.log-stream b')).toHaveTextContent('Warning')
    expect(observability.container.querySelector('.log-stream b')).not.toHaveTextContent('warning')
    expect(observability.container.querySelector('.log-stream')).not.toHaveTextContent(timestamp)
    expect(observability.container.querySelector('.observability-inspector')).toHaveTextContent('trace-syn-09ab')
    expect(eventRow).toMatchObject({ severity: 'warning', timestamp, trace_id: 'trace-syn-09ab' })
    observability.unmount()

    const objectiveRow = Object.freeze({ id: 'slo-1', name: 'Telemetry ingest availability', window_days: 30, target_percent: 99.9, current_percent: 99.76, error_budget_remaining: 18, burn_rate: 2.4, status: 'warning' })
    renderRows(objectiveRow)
    const slo = render(<SloWorkspace {...props([field('name', 'text'), field('window_days', 'integer'), field('target_percent', 'percent'), field('current_percent', 'percent'), field('error_budget_remaining', 'percent'), field('burn_rate', 'number'), field('status', 'select')])} />)
    expect(slo.container.querySelector('.slo-card header')).toHaveTextContent('Warning')
    expect(slo.container.querySelector('.slo-card header')).not.toHaveTextContent('warning')
    expect(slo.container.querySelector('.slo-card header')).toHaveTextContent('30 day window')
    expect(slo.container.querySelector('.slo-card')).toHaveClass('warning')
    expect(objectiveRow).toMatchObject({ status: 'warning', window_days: 30, target_percent: 99.9 })
  })
})
