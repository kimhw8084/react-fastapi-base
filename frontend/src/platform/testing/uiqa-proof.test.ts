import { describe, expect, it } from 'vitest'
import { DimensionProofError, RuntimeDimensionProof } from './uiqa-proof'

const proof = (required: string[] = ['keyboard.tab', 'focus.visible']) => new RuntimeDimensionProof(required, ['keyboard.tab', 'focus.visible', 'browser-computed'])

describe('runtime UIQA dimension proof collector', () => {
  it('rejects unknown dimensions before running an assertion', async () => {
    const collector = proof()
    await expect(collector.prove('not-declared', () => undefined)).rejects.toThrow(DimensionProofError)
    expect(collector.observedDimensions()).toEqual([])
  })

  it('keeps duplicate proof markers idempotent', async () => {
    const collector = proof(['keyboard.tab'])
    await collector.prove('keyboard.tab', () => undefined)
    await collector.prove('keyboard.tab', () => undefined)
    expect(collector.complete()).toEqual(['keyboard.tab'])
  })

  it('does not record a failed assertion as proof', async () => {
    const collector = proof(['keyboard.tab'])
    await expect(collector.prove('keyboard.tab', () => { throw new Error('assertion failed') })).rejects.toThrow('assertion failed')
    expect(collector.observedDimensions()).toEqual([])
    expect(() => collector.complete()).toThrow(/missing=keyboard\.tab/)
  })

  it('fails closed when a required dimension is missing', async () => {
    const collector = proof()
    await collector.prove('keyboard.tab', () => undefined)
    expect(() => collector.complete()).toThrow(/missing=focus\.visible/)
  })

  it('fails closed when an allowed but undeclared dimension is observed', async () => {
    const collector = proof(['keyboard.tab'])
    await collector.prove('browser-computed', () => undefined)
    expect(() => collector.complete()).toThrow(/extra=browser-computed/)
  })

  it('serializes the observed dimensions as an exact stable sort', async () => {
    const collector = proof(['focus.visible', 'keyboard.tab'])
    await collector.prove('focus.visible', () => undefined)
    await collector.prove('keyboard.tab', () => undefined)
    expect(collector.observedDimensions()).toEqual(['focus.visible', 'keyboard.tab'])
    expect(collector.complete()).toEqual(['focus.visible', 'keyboard.tab'])
  })
})
