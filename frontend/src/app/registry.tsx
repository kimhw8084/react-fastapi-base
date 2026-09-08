// Application-owned component registration. Custom workspaces may render any React UI.
import type { ComponentType } from 'react'
import type { WorkspaceContext } from '../platform/workspace/context'
import { Workspace as WorkItemsWorkspace } from '../features/work-items/Workspace'
import { Workspace as ProjectsWorkspace } from '../features/projects/Workspace'
import { Workspace as RackWorkspace } from '../features/racks/Workspace'
import { Workspace as EquipmentWorkspace } from '../features/equipment/Workspace'
import { Workspace as KnowledgeEntrieWorkspace } from '../features/knowledge_entries/Workspace'
import { Workspace as InvestigationWorkspace } from '../features/investigations/Workspace'
import { Workspace as ResearchWorkspace } from '../features/research/Workspace'
import { Workspace as RiskWorkspace } from '../features/risks/Workspace'
import { Workspace as PlanTaskWorkspace } from '../features/plan_tasks/Workspace'
import { Workspace as DiagramDocumentWorkspace } from '../features/diagram_documents/Workspace'
import { Workspace as ProcessMeasurementWorkspace } from '../features/process_measurements/Workspace'
import { Workspace as WaferRunWorkspace } from '../features/wafer_runs/Workspace'
import { Workspace as ManufacturingLotWorkspace } from '../features/manufacturing_lots/Workspace'
import { Workspace as EquipmentStateWorkspace } from '../features/equipment_states/Workspace'
import { Workspace as ProcessRecipeWorkspace } from '../features/process_recipes/Workspace'
import { Workspace as SoftwareServiceWorkspace } from '../features/software_services/Workspace'
import { Workspace as DeliveryRunWorkspace } from '../features/delivery_runs/Workspace'
import { Workspace as ObservabilityEventWorkspace } from '../features/observability_events/Workspace'
import { Workspace as IncidentWorkspace } from '../features/incidents/Workspace'
import { Workspace as ServiceObjectiveWorkspace } from '../features/service_objectives/Workspace'
import { Workspace as SystemWorkspace } from '../features/system/Workspace'
export const workspaceRenderers: Record<string,ComponentType<WorkspaceContext>> = {
  work_items: WorkItemsWorkspace,
  projects: ProjectsWorkspace,
  racks: RackWorkspace,
  equipment: EquipmentWorkspace,
  knowledge_entries: KnowledgeEntrieWorkspace,
  investigations: InvestigationWorkspace,
  research: ResearchWorkspace,
  risks: RiskWorkspace,
  plan_tasks: PlanTaskWorkspace,
  diagram_documents: DiagramDocumentWorkspace,
  process_measurements: ProcessMeasurementWorkspace,
  wafer_runs: WaferRunWorkspace,
  manufacturing_lots: ManufacturingLotWorkspace,
  equipment_states: EquipmentStateWorkspace,
  process_recipes: ProcessRecipeWorkspace,
  software_services: SoftwareServiceWorkspace,
  delivery_runs: DeliveryRunWorkspace,
  observability_events: ObservabilityEventWorkspace,
  incidents: IncidentWorkspace,
  service_objectives: ServiceObjectiveWorkspace,
  system: SystemWorkspace,
}
