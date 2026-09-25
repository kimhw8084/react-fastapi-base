import { describe, expect, it } from 'vitest'
import { dossierTabFallbackText, formatComparisonValue } from './Dossier'

describe('dossier arbitrary revision comparison values', () => {
  it('keeps text and markdown readable without interpreting markup', () => {
    expect(formatComparisonValue('# Runbook\n\n**safe**')).toEqual({ kind: 'text', text: '# Runbook\n\n**safe**' })
  })

  it('renders JSON, arrays and relationship snapshots as structured values', () => {
    expect(formatComparisonValue({ links: [{ entity: 'projects', id: 'p1' }], tags: ['ops'] })).toEqual({
      kind: 'structured',
      text: '{\n  "links": [\n    {\n      "entity": "projects",\n      "id": "p1"\n    }\n  ],\n  "tags": [\n    "ops"\n  ]\n}',
    })
  })

  it('gives empty values a stable comparison marker', () => {
    expect(formatComparisonValue(null)).toEqual({ kind: 'empty', text: '—' })
  })
})

describe('dossier optional section fallback copy', () => {
  it('uses concise product language without implementation adapter jargon', () => {
    const copy = dossierTabFallbackText('actions')
    expect(copy).toBe('No additional record-specific actions are available.')
    expect(copy.toLocaleLowerCase()).not.toContain('adapter')
  })
})
