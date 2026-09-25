import { describe, expect, it } from 'vitest'
import { activeNavigationScrollAdjustment } from './activeNavigationReveal'

describe('active desktop navigation reveal', () => {
  it('leaves an already visible active link at the current scroll position', () => {
    expect(activeNavigationScrollAdjustment({ top: 100, bottom: 700 }, { top: 240, bottom: 278 })).toBe(0)
  })

  it('minimally reveals a link below the scrollport', () => {
    expect(activeNavigationScrollAdjustment({ top: 100, bottom: 700 }, { top: 742, bottom: 780 })).toBe(81)
  })

  it('minimally reveals a link above the scrollport', () => {
    expect(activeNavigationScrollAdjustment({ top: 100, bottom: 700 }, { top: 70, bottom: 108 })).toBe(-31)
  })

  it('fails the no-reveal negative control for an off-screen active link', () => {
    const adjustment = activeNavigationScrollAdjustment({ top: 100, bottom: 700 }, { top: 742, bottom: 780 })
    const remainsVisible = adjustment === 0
    expect(remainsVisible).toBe(false)
  })
})
