import { describe, expect, it } from 'vitest'
import type { WorkspaceDefinition } from '../../generated/schema'
import { migrateWorkspaceView, reconcileWorkspaceView } from './workspaceState'

const definition: WorkspaceDefinition = {
  key: 'fixture', label: 'Fixture', description: '', schema_version: 2, primary_field: 'title',
  fields: [{ key: 'title', label: 'Title', kind: 'text', required: true, nullable: false, max_length: 120, choices: [], minimum: null, maximum: null, step: null, unit: null, precision: null, display_format: null, searchable: true, filterable: true, sortable: true, exportable: true, computed: false, read_only: false }],
  columns: ['title'], capabilities: ['table'], visualizations: ['table'],
  filter_keys: ['title'], sort_keys: ['title'],
}

describe('workspace state reconciliation', () => {
  it('upgrades legacy sort state and removes unsupported fields', () => {
    const migrated = migrateWorkspaceView(definition, ['table'], { sort: 'title', direction: 'asc', columns: [{ colId: 'removed' }, { colId: 'title' }], unknown: 'discard' })
    expect(migrated.schema_version).toBe(2)
    expect(migrated.sorts).toEqual([{ key: 'title', direction: 'asc' }])
    expect(migrated.columns).toEqual([{ colId: 'title' }])
  })

  it('reports a stale local/server conflict while choosing the server winner', () => {
    const local = { search: 'local', sort: 'title', direction: 'asc' }
    const server = migrateWorkspaceView(definition, ['table'], { search: 'server', sort: 'title', direction: 'desc' })
    expect(reconcileWorkspaceView(definition, ['table'], local, server)).toMatchObject({ conflict: true, winner: 'server', view: { search: 'server' } })
  })
})
