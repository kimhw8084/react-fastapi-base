import { useEffect, useState, type ReactNode } from 'react'
import type { ViewDefinition, WorkspaceDefinition } from '../../generated/schema'
import { fieldDisplayText, fieldLabel } from './FieldValue'

export function appliedWorkspaceViewSummary(definition: WorkspaceDefinition, view: ViewDefinition, displayLabel?: string): string {
  const filters = Object.entries(view.filters).map(([key, value]) => {
    const field = definition.fields.find(item => item.key === key)
    return `${fieldLabel(definition, key)}: ${fieldDisplayText(field, value)}`
  })
  const advancedCount = view.advanced_filters?.length ?? 0
  if (advancedCount) filters.push(`${advancedCount} advanced ${advancedCount === 1 ? 'filter' : 'filters'}`)
  const sortLabel = fieldLabel(definition, view.sort)
  const sort = `${sortLabel} ${view.direction === 'asc' ? 'ascending' : 'descending'}`
  const parts = [filters.length ? filters.join(' · ') : 'No filters', `Sort: ${sort}`]
  if (displayLabel) parts.push(`Display: ${displayLabel}`)
  if (view.group_by) parts.push(`Group: ${fieldLabel(definition, view.group_by)}`)
  if (view.density) parts.push(`${view.density === 'compact' ? 'Compact' : 'Comfortable'} density`)
  return parts.join(' · ')
}

export function ResponsiveWorkspaceControls({primary,summary,children}:{primary:ReactNode;summary:string;children:ReactNode}){
  const [compact,setCompact]=useState(()=>window.matchMedia('(max-width: 760px)').matches)
  const [expanded,setExpanded]=useState(false)
  useEffect(()=>{
    const media=window.matchMedia('(max-width: 760px)')
    const update=()=>setCompact(media.matches)
    media.addEventListener('change',update)
    return()=>media.removeEventListener('change',update)
  },[])
  return <div className="responsive-workspace-controls">
    <div className="workspace-controls-primary">{primary}</div>
    <details className="workspace-controls-disclosure" open={!compact||expanded} onToggle={event=>{if(compact)setExpanded(event.currentTarget.open)}}>
      <summary><strong>Filters &amp; view options</strong><span>{summary}</span></summary>
      <div className="workspace-controls-panel">{children}</div>
    </details>
  </div>
}
