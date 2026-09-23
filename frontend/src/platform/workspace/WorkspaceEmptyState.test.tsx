import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DEFAULT_VIEW } from './types'
import { WorkspaceEmptyState } from './WorkspaceEmptyState'

describe('workspace empty-state truth',()=>{
 it('does not label an unfiltered empty dataset as a search miss',()=>{
  render(<WorkspaceEmptyState label="Work items" singular="work item" view={DEFAULT_VIEW} searchInput="" canWrite onViewChange={()=>{}} onSearchInput={()=>{}} onCreate={()=>{}}/>)
  expect(screen.getByRole('heading',{name:'No active work items yet'})).toBeVisible()
  expect(screen.queryByText(/No matching records/)).not.toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Create first work item'})).toBeVisible()
 })
 it('offers filter recovery for a no-match result',()=>{
  const onSearchInput=vi.fn(),onViewChange=vi.fn()
  render(<WorkspaceEmptyState label="Work items" singular="work item" view={{...DEFAULT_VIEW,filters:{status:'blocked'}}} searchInput="nothing" canWrite onViewChange={onViewChange} onSearchInput={onSearchInput} onCreate={()=>{}}/>)
  expect(screen.getByRole('heading',{name:'No matching work items'})).toBeVisible()
  fireEvent.click(screen.getByRole('button',{name:'Clear search and filters'}))
  expect(onSearchInput).toHaveBeenCalledWith('')
  expect(onViewChange).toHaveBeenCalledOnce()
  expect(screen.queryByRole('button',{name:'Create first work item'})).not.toBeInTheDocument()
 })
 it('distinguishes an unfiltered empty archive',()=>{
  render(<WorkspaceEmptyState label="Work items" singular="work item" view={{...DEFAULT_VIEW,archived:true}} searchInput="" canWrite={false} onViewChange={()=>{}} onSearchInput={()=>{}}/>)
  expect(screen.getByRole('heading',{name:'No archived work items'})).toBeVisible()
  expect(screen.getByRole('button',{name:'Show active records'})).toBeVisible()
 })
})
