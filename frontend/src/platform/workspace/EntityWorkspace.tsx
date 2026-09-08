import { useEffect, useMemo, useState, type ComponentType } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { ViewRead } from '../../generated/schema'
import type { WorkspaceContext } from './context'
import type { BaseRecord, WorkspaceAdapter, ProjectionProps } from './types'
import { DEFAULT_VIEW } from './types'
import { readStorage, storageKey, writeStorage } from '../state/storage'
import { BoardWorkspace } from './BoardWorkspace'
import { TableWorkspace } from './TableWorkspace'
import { TimelineWorkspace } from './TimelineWorkspace'
import { CalendarWorkspace } from './CalendarWorkspace'
import { GanttWorkspace } from './GanttWorkspace'
import { DashboardWorkspace } from './DashboardWorkspace'
import { GraphWorkspace } from './GraphWorkspace'
import { RackWorkspace } from './RackWorkspace'
import { SavedViews } from './SavedViews'
import { resolveWorkspaceVisualizations, sanitizeWorkspaceView } from './workspaceState'

interface Props<T extends BaseRecord> extends WorkspaceContext {
  adapter: WorkspaceAdapter<T>
  visualizations?: readonly string[]
  customProjections?: Record<string, ComponentType<ProjectionProps<T>>>
}

export function EntityWorkspace<T extends BaseRecord>(props: Props<T>) {
  const available = useMemo(() => resolveWorkspaceVisualizations(props.adapter.definition, props.visualizations), [props.adapter.definition, props.visualizations])
  const preferenceKey = storageKey(props.appId, props.user, props.tenant, `${props.adapter.key}.working`)
  const [params, setParams] = useSearchParams()
  const queryMode = params.get('visualization')
  const initial = useMemo(() => ({ ...DEFAULT_VIEW, density: props.defaultDensity, visualization: available[0] ?? 'table' }), [available, props.defaultDensity])
  const [view, setView] = useState(() => readStorage(preferenceKey, initial, value => sanitizeWorkspaceView(props.adapter.definition, available, value, props.defaultDensity)))
  const [searchInput, setSearchInput] = useState(view.search)

  useEffect(() => {
    if (!queryMode || !available.includes(queryMode) || queryMode === view.visualization) return
    setView(current => ({ ...current, visualization: queryMode }))
  }, [available, queryMode, view.visualization])

  useEffect(() => {
    const timer = window.setTimeout(() => setView(current => current.search === searchInput ? current : ({ ...current, search: searchInput })), 300)
    return () => window.clearTimeout(timer)
  }, [searchInput])

  useEffect(() => { writeStorage(preferenceKey, view) }, [preferenceKey, view])

  const selectVisualization = (mode: string) => {
    if (!available.includes(mode)) return
    setView(current => ({ ...current, visualization: mode }))
    setParams(current => {
      const next = new URLSearchParams(current)
      if (mode === available[0]) next.delete('visualization')
      else next.set('visualization', mode)
      return next
    })
  }

  const applyView = (saved: ViewRead) => {
    const nextView = sanitizeWorkspaceView(props.adapter.definition, available, saved.definition, props.defaultDensity)
    setView(nextView)
    setSearchInput(nextView.search)
    setParams(current => {
      const next = new URLSearchParams(current)
      next.set('view', saved.id)
      if (nextView.visualization === available[0]) next.delete('visualization')
      else next.set('visualization', nextView.visualization)
      return next
    })
  }

  const projectionSwitch = available.length > 1 ? <div className="segmented visualization-switch" aria-label="Visualization">
    {available.map(mode => <button key={mode} aria-pressed={view.visualization === mode} onClick={() => selectVisualization(mode)}>{mode[0]?.toUpperCase()}{mode.slice(1)}</button>)}
  </div> : undefined

  const viewTools = <div className="workspace-view-tools">
    {projectionSwitch}
    <SavedViews api={props.api} workspace={props.adapter.key} tenant={props.tenant} user={props.user} definition={view} canShare={props.permissions.includes('views.team')} onApply={applyView}/>
  </div>

  const shared = { ...props, view, onViewChange: setView, searchInput, onSearchInput: setSearchInput, viewTools }
  if (view.visualization === 'board' && available.includes('board')) return <BoardWorkspace {...shared}/>
  if (view.visualization === 'timeline' && available.includes('timeline')) return <TimelineWorkspace {...shared}/>
  if (view.visualization === 'calendar' && available.includes('calendar')) return <CalendarWorkspace {...shared}/>
  if (view.visualization === 'gantt' && available.includes('gantt')) return <GanttWorkspace {...shared}/>
  if (view.visualization === 'dashboard' && available.includes('dashboard')) return <DashboardWorkspace {...shared}/>
  if (view.visualization === 'graph' && available.includes('graph')) return <GraphWorkspace {...shared}/>
  if (view.visualization === 'rack' && available.includes('rack')) return <RackWorkspace {...shared}/>
  const CustomProjection = props.customProjections?.[view.visualization]
  if (CustomProjection && available.includes(view.visualization)) return <CustomProjection {...shared}/>
  return <TableWorkspace {...shared}/>
}
