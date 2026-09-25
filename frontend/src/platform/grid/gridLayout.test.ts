import { describe, expect, it } from 'vitest'
import { gridHeightForRows } from './gridLayout'

describe('content-aware grid geometry',()=>{
 it('keeps a sparse result close to its rendered rows',()=>{
  expect(gridHeightForRows(1,'comfortable')).toBe(112)
  expect(gridHeightForRows(2,'comfortable')).toBe(150)
 })
 it('retains a bounded virtualization viewport for large pages',()=>{
  expect(gridHeightForRows(5000,'comfortable')).toBe(520)
  expect(gridHeightForRows(-1,'compact')).toBe(112)
 })
})
