import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusBadge, TrendIndicator } from './primitives'

describe('status and trend semantics',()=>{
 it('does not infer success from a status substring',()=>{
  render(<StatusBadge status="not ready"/>)
  expect(screen.getByText('not ready')).toHaveClass('tone-neutral')
 })
 it('allows an explicit status tone to govern presentation',()=>{
  render(<StatusBadge status="not ready" tone="danger"/>)
  expect(screen.getByText('not ready')).toHaveClass('tone-danger')
 })
 it('keeps trend direction separate from desirability',()=>{
  const {rerender}=render(<TrendIndicator value={5} desirability="higher-is-better"/>)
  expect(screen.getByText('5.0%')).toHaveClass('positive')
  rerender(<TrendIndicator value={5} desirability="lower-is-better"/>)
  expect(screen.getByText('5.0%')).toHaveClass('negative')
  rerender(<TrendIndicator value={-5} desirability="lower-is-better"/>)
  expect(screen.getByText('5.0%')).toHaveClass('positive')
 })
})
