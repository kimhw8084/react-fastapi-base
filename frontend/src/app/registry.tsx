// Application-owned component registration. Feature bundles load only when a workspace route needs them.
import { lazy, Suspense, type ComponentType } from 'react'
import type { WorkspaceContext } from '../platform/workspace/context'

type WorkspaceRenderer=ComponentType<WorkspaceContext>
const feature=(loader:()=>Promise<{Workspace:ComponentType<WorkspaceContext>}>):WorkspaceRenderer=>{
  const LazyWorkspace=lazy(()=>loader().then(module=>({default:module.Workspace})))
  return function LazyWorkspaceRoute(props:WorkspaceContext){return <Suspense fallback={<p role="status">Loading workspace…</p>}><LazyWorkspace {...props}/></Suspense>}
}

export const workspaceRenderers: Record<string,WorkspaceRenderer> = {
  work_items: feature(()=>import('../features/work-items/Workspace')),
  projects: feature(()=>import('../features/projects/Workspace')),
  racks: feature(()=>import('../features/racks/Workspace')),
  equipment: feature(()=>import('../features/equipment/Workspace')),
  knowledge_entries: feature(()=>import('../features/knowledge_entries/Workspace')),
  investigations: feature(()=>import('../features/investigations/Workspace')),
  research: feature(()=>import('../features/research/Workspace')),
  risks: feature(()=>import('../features/risks/Workspace')),
  plan_tasks: feature(()=>import('../features/plan_tasks/Workspace')),
  diagram_documents: feature(()=>import('../features/diagram_documents/Workspace')),
  process_measurements: feature(()=>import('../features/process_measurements/Workspace')),
  wafer_runs: feature(()=>import('../features/wafer_runs/Workspace')),
  manufacturing_lots: feature(()=>import('../features/manufacturing_lots/Workspace')),
  equipment_states: feature(()=>import('../features/equipment_states/Workspace')),
  process_recipes: feature(()=>import('../features/process_recipes/Workspace')),
  software_services: feature(()=>import('../features/software_services/Workspace')),
  delivery_runs: feature(()=>import('../features/delivery_runs/Workspace')),
  observability_events: feature(()=>import('../features/observability_events/Workspace')),
  incidents: feature(()=>import('../features/incidents/Workspace')),
  service_objectives: feature(()=>import('../features/service_objectives/Workspace')),
  system: feature(()=>import('../features/system/Workspace')),
}
