import { describe, expect, it } from 'vitest'
import { correlation, cusum, linearRegression, npChart, pChart, xbarS } from './spcModel'

describe('statistical parity fixtures',()=>{
 it('matches the server-owned chart fixtures',()=>{
  expect(xbarS([[10,11,9,10],[10,10,11,9],[12,11,10,11],[9,10,9,10]]).subgroupSize).toBe(4)
  expect(pChart([1,2,1,3],[10,10,10,10]).center).toBeCloseTo(.175)
  expect(npChart([1,2,1],10).center).toBeCloseTo(4/3)
  expect(cusum([10,10,12],10).positive.at(-1)).toBeCloseTo(2)
 })
 it('matches correlation and regression fixtures with zero-variance guards',()=>{
  expect(correlation([1,2,3],[2,4,6])).toBeCloseTo(1)
  expect(linearRegression([1,2,3],[2,4,6])).toMatchObject({slope:2,intercept:0,rSquared:1})
  expect(()=>correlation([1,1,1],[2,3,4])).toThrow('zero variance')
  expect(()=>linearRegression([1,1,1],[2,3,4])).toThrow('zero x variance')
 })
})
