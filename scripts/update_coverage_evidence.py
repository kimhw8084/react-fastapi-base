#!/usr/bin/env python3
"""Synchronize roadmap implementation evidence from concrete platform source.

This deliberately promotes source-backed items only to `partial`, never `stable`.
Stable still requires the full release Definition of Done (real React build,
accessibility/visual/E2E evidence, documentation and performance where relevant).
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

EVIDENCE: dict[str,str] = {}
def add(source: str, names: str):
    for name in names.split(): EVIDENCE[name]=source

add('frontend/src/platform/ui/primitives.tsx','''Heading Subheading BodyText SecondaryText Caption Label MonoText InlineCode CodeBlock Link ExternalLink TruncatedText ExpandableText CopyableText KeyValue DefinitionList MetricValue MetricDelta Timestamp RelativeTime Duration UserIdentity EmptyValue Button IconButton SplitButton ButtonGroup ToggleButton ToggleGroup SegmentedControl Checkbox Radio Switch Slider RangeSlider LinkButton CopyButton FavoriteButton PinButton RefreshButton Badge StatusBadge StatusDot Chip Tag CountBadge Avatar AvatarGroup PresenceIndicator ProgressBar ProgressRing Spinner Skeleton HealthIndicator TrendIndicator SeverityIndicator SLAIndicator Banner InlineAlert''')
add('frontend/src/platform/ui/shellVariants.tsx','''AlertDialog ConfirmDialog DestructiveConfirmDialog FormDialog WizardDialog DossierDialog ComparisonDialog FullScreenDialog DrawerLeft DrawerRight DrawerBottom InspectorDrawer DetailsDrawer Popover Dropdown ComboDropdown HoverCard ContextMenu ActionMenu AnchoredFlyout NotificationDrawer SideSheet SidecarPanel DockedPanel CollapsiblePanel FloatingInspector SearchPalette QuickSwitcher''')
add('frontend/src/platform/ui/Dialog.tsx','Modal')
add('frontend/src/platform/ui/FloatingPanelShell.tsx','FloatingPanel')
add('frontend/src/platform/ui/OverlayShell.tsx','BottomSheet')
add('frontend/src/platform/ui/SplitPaneShell.tsx','SplitPane ResizablePane MasterDetailPane')
add('frontend/src/platform/commands/CommandPalette.tsx','CommandPalette')
add('frontend/src/platform/workspace/FieldInput.tsx','''TextInput Textarea IntegerInput DecimalInput ScientificNumberInput PercentInput UnitAwareNumberInput EmailInput URLInput Select MultiSelect DatePicker DateTimePicker DurationInput JSONEditor CodeEditor MarkdownEditor EngineeringUnitInput''')
add('frontend/src/platform/workspace/RecordForm.tsx','DynamicSchemaForm SectionedForm FormWorkspace InlineEditableForm')
add('frontend/src/platform/workspace/BulkEditDialog.tsx','BulkEditForm')
add('frontend/src/features/work-items/Attachments.tsx','FileInput AttachmentGallery')
add('frontend/src/platform/grid/DataGrid.tsx','''SimpleTable DataGrid VirtualizedGrid EditableGrid ServerSideGrid GroupedGrid SelectableGrid BulkActionGrid ContextMenuGrid PinnedColumnGrid''')
add('frontend/src/platform/workspace/TableWorkspace.tsx','TableWorkspace MasterDetailWorkspace DetailWorkspace')
add('frontend/src/platform/workspace/BoardWorkspace.tsx','BoardWorkspace KanbanWorkspace KanbanBoard')
add('frontend/src/platform/workspace/DashboardWorkspace.tsx','DashboardWorkspace DashboardGrid')
add('frontend/src/platform/workspace/TimelineWorkspace.tsx','TimelineWorkspace SimpleTimeline HorizontalTimeline EventTimeline')
add('frontend/src/platform/workspace/CalendarWorkspace.tsx','CalendarWorkspace Calendar')
add('frontend/src/platform/workspace/GanttWorkspace.tsx','GanttWorkspace GanttChart')
add('frontend/src/platform/workspace/PlanningWorkspace.tsx','''DependencyGantt Roadmap MilestoneTimeline ReleasePlan Milestones''')
add('frontend/src/platform/workspace/GraphWorkspace.tsx','TopologyWorkspace DependencyGraph ServiceTopology NetworkTopology NetworkGraph GraphChart')
add('frontend/src/platform/workspace/DiagramDesignerWorkspace.tsx','''DiagramWorkspace FlowDiagram ArchitectureDiagram ProcessFlow WorkflowGraph DAG NodeEditor EdgeEditor ZoomControls FitView SelectionBox MultiSelectCanvas''')
add('frontend/src/platform/workspace/RackWorkspace.tsx','RackWorkspace RackElevation CabinetView SlotView PortConnectionDiagram PortMap ConnectorMap')
add('frontend/src/platform/workspace/KnowledgeWorkspace.tsx','DocumentationWorkspace RunbookViewer MarkdownViewer')
add('frontend/src/platform/workspace/InvestigationWorkspace.tsx','InvestigationWorkspace')
add('frontend/src/platform/workspace/RiskWorkspace.tsx','CapabilityAnalysis')
add('frontend/src/platform/workspace/SpcWorkspace.tsx','''AnalyticalWorkspace SPCWorkspace RunChart IndividualsMovingRange EWMAChart ControlLimitsChart CpCpkPanel PpPpkPanel ParetoDefects SPCDashboard ControlChartSuite ParameterTrend ParetoDefect CapabilityAnalysis''')
add('frontend/src/packs/semiconductor/WaferWorkspace.tsx','''WaferWorkspace WaferMap WaferBinMap DefectMap DefectDensityMap WaferSelectionMap WaferZoneOverlay DieGrid''')
add('frontend/src/packs/semiconductor/LotTravelerWorkspace.tsx','''LotTraveler LotHistory ProcessRoute ProcessStepTimeline WIPByStep''')
add('frontend/src/packs/semiconductor/EquipmentStateWorkspace.tsx','''EquipmentStatePanel EquipmentStateTimeline ModuleStatePanel ChamberStatePanel AvailabilityPanel UtilizationPanel MTBF MTTR AlarmTimeline MaintenanceTimeline''')
add('frontend/src/packs/semiconductor/RecipeWorkspace.tsx','''RecipeEditor RecipeParameterGrid RecipeDiff RecipeVersionHistory ProcessWindow ParameterLimits GoldenRecipeComparison''')
add('frontend/src/packs/software-engineering/DeliveryWorkspace.tsx','''PipelineGraph JobGraph BuildTimeline DeploymentTimeline ReleaseDashboard''')
add('frontend/src/packs/software-engineering/ObservabilityWorkspace.tsx','''LogWorkspace MetricsExplorer LogExplorer TraceExplorer TraceWaterfall''')
add('frontend/src/packs/software-engineering/IncidentWorkspace.tsx','''IncidentWorkspace IncidentCommandCenter AlertConsole''')
add('frontend/src/packs/software-engineering/SloWorkspace.tsx','''SLODashboard ErrorBudget''')
add('frontend/src/platform/ui/AppShell.tsx','AppShell SidebarShell HeaderContent HeaderToolbarContent')
add('frontend/src/platform/ui/WorkspaceShell.tsx','FullHeightWorkspace DenseOperationsWorkspace CanvasWorkspace')
add('frontend/src/platform/ui/SplitPaneShell.tsx','SplitViewWorkspace SplitHorizontal SplitVertical ResizableSplit InspectorLayout MasterDetail')
add('backend/app/profiles/company/identity.py','AccessKeyIdentity')
add('backend/app/platform/security.py','Authorization TenantIsolation RateLimits')
add('backend/app/platform/database.py','Transactions DirectDatabaseSDK')
add('backend/app/platform/migrations.py','MigrationHistory ConfigDatabaseMigrations MigrationRehearsal')
add('backend/app/platform/attachments.py','AttachmentsProtection')
add('backend/app/platform/idempotency.py','Idempotency')
add('backend/app/platform/audit.py','AuditPersistence RevisionRevert')
add('backend/app/platform/backup.py','BackupManifest IsolatedRestore')
add('backend/app/platform/views.py','SavedViewsPersistence')
add('scripts/generate_contracts.py','GeneratedAPIContracts APIContractDrift')
add('scripts/entity_generator.py','ApplicationGenerator WorkspaceGenerator')
add('scripts/template_tools.py','UpgradePlanner UpgradeApply UpgradeRollback')
add('scripts/check_architecture.py','ArchitectureRules')
add('scripts/security_source_check.py','SecretScanning')
add('scripts/performance_check.py','PerformanceBudgets')
add('scripts/checkpoint.py','SourceCheckpoints')
add('scripts/catalog.py','CatalogCompleteness')
add('backend/app/platform/jobs.py','DurableJobs')
add('backend/app/platform/events.py','RealtimeBus')
add('backend/app/platform/webhooks.py','WebhooksOutbound IntegrationCredentials')
add('backend/app/platform/notifications.py','NotificationDelivery')
add('backend/app/platform/middleware.py','StructuredLogging')
add('frontend/src/features/system/Workspace.tsx','UserDirectory MemberTable RoleManager PermissionMatrix FeatureFlagManager NotificationPreferences AuditConsole HealthDashboard RuntimeDiagnostics APIConnectivity EnvironmentInfo')
add('frontend/src/app/Application.tsx','TenantSelector ThemeSettings Preferences')
add('frontend/src/app/lab/ExperienceLab.tsx','ExperienceLab ThemeStudio')


def main()->int:
    roadmap_path=ROOT/'catalog/roadmap.json'; roadmap=json.loads(roadmap_path.read_text())
    known={row['id'] for row in roadmap['entries']}
    missing=sorted(set(EVIDENCE)-known)
    if missing: raise SystemExit('Evidence IDs absent from roadmap: '+', '.join(missing))
    evidence=[]
    for row in roadmap['entries']:
        source=EVIDENCE.get(row['id'])
        if not source: continue
        path=ROOT/source
        if not path.is_file(): raise SystemExit(f'Missing evidence source for {row["id"]}: {source}')
        if row['maturity']=='planned': row['maturity']='partial'
        row['demo_families']=sorted(set(row.get('demo_families',[])))
        row['note']=f'Concrete reusable implementation exists in {source}; full production Definition of Done is not yet certified.'
        evidence.append({'id':row['id'],'source':source,'implementation_status':'implemented-source','release_maturity':row['maturity']})
    roadmap_path.write_text(json.dumps(roadmap,indent=2)+'\n')
    (ROOT/'catalog/implementation-evidence.json').write_text(json.dumps({'schema_version':1,'entries':evidence,'stable_promotions_by_this_script':0},indent=2)+'\n')
    print(f'Implementation evidence synchronized: {len(evidence)} retained capabilities have concrete source; none were auto-promoted to stable.')
    return 0
if __name__=='__main__':raise SystemExit(main())
