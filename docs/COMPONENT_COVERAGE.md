# Component and platform coverage

This is an explicit delivery ledger, not a percentage-complete claim.

## Interactive families

| Family | Capabilities | Remaining limits |
|---|---|---|
| Data tables | search; sort; grouping; selection; pagination; CSV export | Client-side reference grid; large data uses the separate AG Grid adapter.; No pivot or multi-range editing in this widget. |
| Work boards | status lanes; drag & drop; keyboard selector; detail events | Local fixture only; server transitions must enforce domain policy. |
| Gantt & planning | task bars; dependency validation; zoom; date editing; progress | Finish-to-start constraints only.; Critical path, baselines and automatic resource scheduling are not implemented. |
| Calendar | month view; date selection; event creation; keyboard focus | No recurrence or calendar-provider synchronization. |
| Equipment timeline | state intervals; legend; interval inspection | Synthetic state labels; not SEMI E10/E116 compliance. |
| Rack elevation | 42U elevation; front/rear presentation; placement validation; power summary | No live electrical safety assessment, cables or port modeling. |
| Wafer & die maps | die inspection; bin filter; yield summary; arrow-key navigation | Synthetic circular die grid; no proprietary wafer-format parser.; No SEMI format or manufacturing compliance claim. |
| Process analytics | line; area; bar; scatter; sample statistics; point-limit detection | Not a validated SPC rule engine.; No Cpk/Ppk, subgroup charts, or measurement-system analysis. |
| Charts & matrices | Pareto bars; donut; heatmap; selection | Fixed synthetic fixture; adapters must provide real semantics. |
| Service topology | node/edge viewer; selection; zoom; keyboard inspection | No graph authoring, auto-layout or workflow execution. |
| Trace waterfall | span timeline; depth; duration; span inspection | No live OpenTelemetry ingestion adapter yet. |
| Log explorer | search; severity filter; detail events; bounded viewport | Not connected to a live stream or retention backend. |
| Revision comparison | line comparison; editable inputs; safe rendering | Positional line diff, not semantic merge or LCS alignment. |
| Engineering forms | required fields; finite numeric values; unit selection; validation; readonly | No automatic unit conversion or domain validation rules. |
| Windows & overlays | modal; drawer; sheet; fullscreen; wizard; confirmation; popover; toast; dirty guard | No docking engine or browser-window tear-out. |
| Configuration editor | object validation; formatting; size limit; change event | JSON syntax only; app-specific schemas require an adapter. |
| Carrier slot map | 25-slot map; slot inspection; occupancy validation; safe local reassignment | Not an equipment controller or SEMI E87/E90 implementation. |
| Lot traveler | process steps; prerequisite checks; hold/resume; completion | Synthetic route and state machine only; no manufacturing authorization or equipment execution. |
| Equipment floor plan | logical coordinates; asset inspection; placement validation; keyboard selection | Not a physical-clearance, facilities or safety design tool. |
| Permission matrix | role/action matrix; grant toggles; read-only preview | Preview changes never grant actual access; server policy remains authoritative. |
| Split workspace | file navigation; resizing; arrow-key resizing; range alternative | No floating-window or docking engine. |
| CI/CD pipeline | stage status; stage inspection; status simulation | No CI execution, credentials, remote provider or deployments. |
| Notification center | unread counts; filtering; mark read/unread; mark all read | No notification-delivery backend or realtime connection. |

## Full retained scope

All entries remain required until explicitly approved otherwise. `partial` means a demonstration covers part of the contract, not a certified reusable implementation.

| Required item | Category | Status | Related examples |
|---|---|---|---|
| Heading | Typography and content | partial | — |
| Subheading | Typography and content | partial | — |
| BodyText | Typography and content | partial | — |
| SecondaryText | Typography and content | partial | — |
| Caption | Typography and content | partial | — |
| Label | Typography and content | partial | — |
| MonoText | Typography and content | partial | — |
| InlineCode | Typography and content | partial | — |
| CodeBlock | Typography and content | partial | — |
| Link | Typography and content | partial | — |
| ExternalLink | Typography and content | partial | — |
| TruncatedText | Typography and content | partial | — |
| ExpandableText | Typography and content | partial | — |
| CopyableText | Typography and content | partial | — |
| KeyValue | Typography and content | partial | — |
| DefinitionList | Typography and content | partial | — |
| MetricValue | Typography and content | partial | — |
| MetricDelta | Typography and content | partial | — |
| Timestamp | Typography and content | partial | — |
| RelativeTime | Typography and content | partial | — |
| Duration | Typography and content | partial | — |
| UserIdentity | Typography and content | partial | — |
| EmptyValue | Typography and content | partial | — |
| Button | Controls | partial | — |
| IconButton | Controls | partial | — |
| SplitButton | Controls | partial | — |
| ButtonGroup | Controls | partial | — |
| ToggleButton | Controls | partial | — |
| ToggleGroup | Controls | partial | — |
| SegmentedControl | Controls | partial | — |
| Checkbox | Controls | partial | — |
| Radio | Controls | partial | — |
| Switch | Controls | partial | — |
| Slider | Controls | partial | — |
| RangeSlider | Controls | partial | — |
| LinkButton | Controls | partial | — |
| CopyButton | Controls | partial | — |
| FavoriteButton | Controls | partial | — |
| PinButton | Controls | partial | — |
| RefreshButton | Controls | partial | — |
| Badge | Indicators | partial | — |
| StatusBadge | Indicators | partial | — |
| StatusDot | Indicators | partial | — |
| Chip | Indicators | partial | — |
| Tag | Indicators | partial | — |
| CountBadge | Indicators | partial | — |
| Avatar | Indicators | partial | — |
| AvatarGroup | Indicators | partial | — |
| PresenceIndicator | Indicators | partial | — |
| ProgressBar | Indicators | partial | — |
| ProgressRing | Indicators | partial | — |
| Spinner | Indicators | partial | — |
| Skeleton | Indicators | partial | — |
| HealthIndicator | Indicators | partial | — |
| TrendIndicator | Indicators | partial | — |
| SeverityIndicator | Indicators | partial | — |
| SLAIndicator | Indicators | partial | — |
| Modal | Windows and overlays | partial | windows |
| AlertDialog | Windows and overlays | partial | — |
| ConfirmDialog | Windows and overlays | partial | windows |
| DestructiveConfirmDialog | Windows and overlays | partial | — |
| FormDialog | Windows and overlays | partial | windows |
| WizardDialog | Windows and overlays | partial | windows |
| DossierDialog | Windows and overlays | partial | — |
| ComparisonDialog | Windows and overlays | partial | — |
| FullScreenDialog | Windows and overlays | partial | windows |
| DrawerLeft | Windows and overlays | partial | — |
| DrawerRight | Windows and overlays | partial | windows |
| DrawerBottom | Windows and overlays | partial | — |
| InspectorDrawer | Windows and overlays | partial | windows |
| DetailsDrawer | Windows and overlays | partial | — |
| Popover | Windows and overlays | partial | windows |
| Dropdown | Windows and overlays | partial | — |
| ComboDropdown | Windows and overlays | partial | — |
| HoverCard | Windows and overlays | partial | — |
| Tooltip | Windows and overlays | partial | windows |
| ContextMenu | Windows and overlays | partial | — |
| Menu | Windows and overlays | planned | — |
| Submenu | Windows and overlays | planned | — |
| ActionMenu | Windows and overlays | partial | — |
| AnchoredFlyout | Windows and overlays | partial | — |
| FloatingPanel | Windows and overlays | partial | — |
| CommandPalette | Windows and overlays | partial | — |
| SearchPalette | Windows and overlays | partial | — |
| QuickSwitcher | Windows and overlays | partial | — |
| Toast | Windows and overlays | partial | windows |
| ToastStack | Windows and overlays | partial | windows |
| NotificationCenter | Windows and overlays | partial | notifications |
| NotificationDrawer | Windows and overlays | partial | — |
| Banner | Windows and overlays | partial | — |
| InlineAlert | Windows and overlays | partial | — |
| BottomSheet | Windows and overlays | partial | windows |
| SideSheet | Windows and overlays | partial | — |
| MasterDetailPane | Windows and overlays | partial | split |
| SplitPane | Windows and overlays | partial | split |
| ResizablePane | Windows and overlays | partial | split |
| SidecarPanel | Windows and overlays | partial | — |
| DockedPanel | Windows and overlays | partial | — |
| CollapsiblePanel | Windows and overlays | partial | — |
| FloatingInspector | Windows and overlays | partial | — |
| DockWorkspace | Windows and overlays | planned | — |
| TextInput | Forms and inputs | partial | — |
| Textarea | Forms and inputs | partial | — |
| PasswordInput | Forms and inputs | planned | — |
| SearchInput | Forms and inputs | planned | — |
| IntegerInput | Forms and inputs | partial | — |
| DecimalInput | Forms and inputs | partial | — |
| ScientificNumberInput | Forms and inputs | partial | — |
| CurrencyInput | Forms and inputs | planned | — |
| PercentInput | Forms and inputs | partial | — |
| UnitAwareNumberInput | Forms and inputs | partial | — |
| EmailInput | Forms and inputs | partial | — |
| PhoneInput | Forms and inputs | planned | — |
| URLInput | Forms and inputs | partial | — |
| Select | Forms and inputs | partial | — |
| MultiSelect | Forms and inputs | partial | — |
| Combobox | Forms and inputs | planned | — |
| Autocomplete | Forms and inputs | planned | — |
| TagInput | Forms and inputs | planned | — |
| TokenInput | Forms and inputs | planned | — |
| SearchableSelector | Forms and inputs | planned | — |
| CheckboxGroup | Forms and inputs | planned | — |
| RadioGroup | Forms and inputs | planned | — |
| DatePicker | Forms and inputs | partial | — |
| TimePicker | Forms and inputs | planned | — |
| DateTimePicker | Forms and inputs | partial | — |
| DateRangePicker | Forms and inputs | planned | — |
| MonthPicker | Forms and inputs | planned | — |
| YearPicker | Forms and inputs | planned | — |
| DurationInput | Forms and inputs | partial | — |
| TimezonePicker | Forms and inputs | planned | — |
| FileInput | Forms and inputs | partial | — |
| MultiFileUpload | Forms and inputs | planned | — |
| DragDropUpload | Forms and inputs | planned | — |
| ImageUpload | Forms and inputs | planned | — |
| ColorPicker | Forms and inputs | planned | — |
| IconPicker | Forms and inputs | planned | — |
| KeyValueEditor | Forms and inputs | planned | — |
| ArrayEditor | Forms and inputs | planned | — |
| ObjectEditor | Forms and inputs | planned | — |
| JSONEditor | Forms and inputs | partial | json |
| YAMLEditor | Forms and inputs | planned | — |
| CodeEditor | Forms and inputs | partial | — |
| MarkdownEditor | Forms and inputs | partial | — |
| RichTextEditor | Forms and inputs | planned | — |
| CronBuilder | Forms and inputs | planned | — |
| ExpressionBuilder | Forms and inputs | planned | — |
| FilterBuilder | Forms and inputs | planned | — |
| QueryBuilder | Forms and inputs | planned | — |
| RuleBuilder | Forms and inputs | planned | — |
| FormulaBuilder | Forms and inputs | planned | — |
| CoordinateInput | Forms and inputs | planned | — |
| RangeInput | Forms and inputs | planned | — |
| ToleranceInput | Forms and inputs | partial | forms |
| EngineeringUnitInput | Forms and inputs | partial | forms |
| DynamicSchemaForm | Forms and inputs | partial | — |
| TabbedForm | Forms and inputs | planned | — |
| SectionedForm | Forms and inputs | partial | forms |
| WizardForm | Forms and inputs | planned | — |
| InlineEditableForm | Forms and inputs | partial | — |
| BulkEditForm | Forms and inputs | partial | — |
| SimpleTable | Tables and grids | partial | tables |
| DataGrid | Tables and grids | partial | tables |
| VirtualizedGrid | Tables and grids | partial | — |
| EditableGrid | Tables and grids | partial | — |
| InlineEditGrid | Tables and grids | planned | — |
| ServerSideGrid | Tables and grids | partial | — |
| InfiniteGrid | Tables and grids | planned | — |
| GroupedGrid | Tables and grids | partial | tables |
| TreeGrid | Tables and grids | planned | — |
| PivotGrid | Tables and grids | planned | — |
| CrossTabGrid | Tables and grids | planned | — |
| MasterDetailGrid | Tables and grids | planned | — |
| NestedGrid | Tables and grids | planned | — |
| ComparisonGrid | Tables and grids | planned | — |
| DiffGrid | Tables and grids | planned | — |
| MatrixGrid | Tables and grids | planned | — |
| PropertyGrid | Tables and grids | planned | — |
| LogGrid | Tables and grids | planned | — |
| EventGrid | Tables and grids | planned | — |
| MetricGrid | Tables and grids | planned | — |
| SelectableGrid | Tables and grids | partial | tables |
| RangeSelectableGrid | Tables and grids | planned | — |
| BulkActionGrid | Tables and grids | partial | tables |
| ContextMenuGrid | Tables and grids | partial | — |
| PinnedColumnGrid | Tables and grids | partial | — |
| PinnedRowGrid | Tables and grids | planned | — |
| SummaryRowGrid | Tables and grids | planned | — |
| CalculatedColumnGrid | Tables and grids | planned | — |
| FormulaColumnGrid | Tables and grids | planned | — |
| TableWorkspace | Workspace archetypes | partial | tables |
| BoardWorkspace | Workspace archetypes | partial | boards |
| DashboardWorkspace | Workspace archetypes | partial | — |
| FormWorkspace | Workspace archetypes | partial | forms |
| DetailWorkspace | Workspace archetypes | partial | — |
| MasterDetailWorkspace | Workspace archetypes | partial | split |
| SplitViewWorkspace | Workspace archetypes | partial | split |
| TimelineWorkspace | Workspace archetypes | partial | — |
| GanttWorkspace | Workspace archetypes | partial | gantt |
| CalendarWorkspace | Workspace archetypes | partial | calendar |
| SchedulerWorkspace | Workspace archetypes | planned | — |
| KanbanWorkspace | Workspace archetypes | partial | boards |
| TreeWorkspace | Workspace archetypes | planned | — |
| HierarchyWorkspace | Workspace archetypes | planned | — |
| DiagramWorkspace | Workspace archetypes | partial | — |
| TopologyWorkspace | Workspace archetypes | partial | topology |
| ProcessFlowWorkspace | Workspace archetypes | planned | — |
| MapWorkspace | Workspace archetypes | planned | — |
| FloorPlanWorkspace | Workspace archetypes | partial | floorplan |
| RackWorkspace | Workspace archetypes | partial | rack |
| AnalyticalWorkspace | Workspace archetypes | partial | — |
| SPCWorkspace | Workspace archetypes | partial | — |
| WaferWorkspace | Workspace archetypes | partial | wafer |
| LogWorkspace | Workspace archetypes | partial | — |
| IncidentWorkspace | Workspace archetypes | partial | — |
| ComparisonWorkspace | Workspace archetypes | planned | — |
| InvestigationWorkspace | Workspace archetypes | partial | — |
| DocumentationWorkspace | Workspace archetypes | partial | — |
| CodeWorkspace | Workspace archetypes | planned | — |
| Line | Charts and visualizations | partial | process |
| MultiLine | Charts and visualizations | planned | — |
| Area | Charts and visualizations | partial | process |
| StackedArea | Charts and visualizations | planned | — |
| Bar | Charts and visualizations | partial | process |
| GroupedBar | Charts and visualizations | planned | — |
| StackedBar | Charts and visualizations | planned | — |
| HorizontalBar | Charts and visualizations | partial | charts |
| ComboChart | Charts and visualizations | planned | — |
| Scatter | Charts and visualizations | partial | process |
| Bubble | Charts and visualizations | planned | — |
| JitterScatter | Charts and visualizations | planned | — |
| Histogram | Charts and visualizations | planned | — |
| BoxPlot | Charts and visualizations | planned | — |
| Violin | Charts and visualizations | planned | — |
| Beeswarm | Charts and visualizations | planned | — |
| Pie | Charts and visualizations | planned | — |
| Donut | Charts and visualizations | partial | charts |
| Pareto | Charts and visualizations | planned | — |
| Waterfall | Charts and visualizations | planned | — |
| Funnel | Charts and visualizations | planned | — |
| Gauge | Charts and visualizations | planned | — |
| Bullet | Charts and visualizations | planned | — |
| ProgressGauge | Charts and visualizations | planned | — |
| Radar | Charts and visualizations | planned | — |
| Heatmap | Charts and visualizations | partial | charts |
| CalendarHeatmap | Charts and visualizations | planned | — |
| Treemap | Charts and visualizations | planned | — |
| Sunburst | Charts and visualizations | planned | — |
| Sankey | Charts and visualizations | planned | — |
| Chord | Charts and visualizations | planned | — |
| ParallelCoordinates | Charts and visualizations | planned | — |
| GraphChart | Charts and visualizations | partial | — |
| NetworkGraph | Charts and visualizations | partial | topology |
| RangeChart | Charts and visualizations | planned | — |
| ConfidenceBandChart | Charts and visualizations | planned | — |
| Sparkline | Charts and visualizations | planned | — |
| MicroBar | Charts and visualizations | planned | — |
| MiniTrend | Charts and visualizations | planned | — |
| RunChart | Statistical process engineering | partial | — |
| XbarRChart | Statistical process engineering | planned | — |
| XbarSChart | Statistical process engineering | planned | — |
| IndividualsMovingRange | Statistical process engineering | partial | — |
| PChart | Statistical process engineering | planned | — |
| NPChart | Statistical process engineering | planned | — |
| CChart | Statistical process engineering | planned | — |
| UChart | Statistical process engineering | planned | — |
| CUSUMChart | Statistical process engineering | planned | — |
| EWMAChart | Statistical process engineering | partial | — |
| ControlLimitsChart | Statistical process engineering | partial | process |
| CapabilityHistogram | Statistical process engineering | planned | — |
| CpCpkPanel | Statistical process engineering | partial | — |
| PpPpkPanel | Statistical process engineering | partial | — |
| DistributionComparison | Statistical process engineering | planned | — |
| CorrelationMatrix | Statistical process engineering | planned | — |
| ScatterMatrix | Statistical process engineering | planned | — |
| RegressionPlot | Statistical process engineering | planned | — |
| ResidualPlot | Statistical process engineering | planned | — |
| ParetoDefects | Statistical process engineering | partial | — |
| ProcessWindowChart | Statistical process engineering | planned | — |
| ToleranceBandChart | Statistical process engineering | planned | — |
| GoldenSampleComparison | Statistical process engineering | planned | — |
| SimpleTimeline | Planning and time | partial | — |
| VerticalTimeline | Planning and time | planned | — |
| HorizontalTimeline | Planning and time | partial | — |
| EventTimeline | Planning and time | partial | — |
| IncidentTimeline | Planning and time | planned | — |
| StateTimeline | Planning and time | partial | timeline |
| MilestoneTimeline | Planning and time | partial | — |
| GanttChart | Planning and time | partial | gantt |
| DependencyGantt | Planning and time | partial | gantt |
| ResourceGantt | Planning and time | planned | — |
| PortfolioGantt | Planning and time | planned | — |
| Roadmap | Planning and time | partial | — |
| ResourceSchedule | Planning and time | planned | — |
| MachineSchedule | Planning and time | planned | — |
| PeopleSchedule | Planning and time | planned | — |
| ShiftSchedule | Planning and time | planned | — |
| Calendar | Planning and time | partial | calendar |
| MonthCalendar | Planning and time | partial | calendar |
| WeekCalendar | Planning and time | planned | — |
| DayCalendar | Planning and time | planned | — |
| Agenda | Planning and time | planned | — |
| ResourceCalendar | Planning and time | planned | — |
| SwimlaneTimeline | Planning and time | planned | — |
| Burndown | Planning and time | planned | — |
| Burnup | Planning and time | planned | — |
| CumulativeFlow | Planning and time | planned | — |
| CapacityTimeline | Planning and time | planned | — |
| UtilizationTimeline | Planning and time | planned | — |
| FlowDiagram | Diagrams and canvases | partial | — |
| DependencyGraph | Diagrams and canvases | partial | topology |
| ServiceTopology | Diagrams and canvases | partial | topology |
| NetworkTopology | Diagrams and canvases | partial | — |
| ArchitectureDiagram | Diagrams and canvases | partial | — |
| ProcessFlow | Diagrams and canvases | partial | — |
| ManufacturingRoute | Diagrams and canvases | planned | — |
| DAG | Diagrams and canvases | partial | — |
| WorkflowGraph | Diagrams and canvases | partial | — |
| StateMachine | Diagrams and canvases | planned | — |
| DecisionTree | Diagrams and canvases | planned | — |
| OrgChart | Diagrams and canvases | planned | — |
| GenealogyGraph | Diagrams and canvases | planned | — |
| TraceabilityGraph | Diagrams and canvases | planned | — |
| DataLineage | Diagrams and canvases | planned | — |
| MindMap | Diagrams and canvases | planned | — |
| SwimlaneDiagram | Diagrams and canvases | planned | — |
| PortConnectionDiagram | Diagrams and canvases | partial | — |
| NodeEditor | Diagrams and canvases | partial | — |
| EdgeEditor | Diagrams and canvases | partial | — |
| MiniMap | Diagrams and canvases | planned | — |
| ZoomControls | Diagrams and canvases | partial | topology |
| FitView | Diagrams and canvases | partial | topology |
| SelectionBox | Diagrams and canvases | partial | — |
| MultiSelectCanvas | Diagrams and canvases | partial | — |
| RackElevation | Physical and spatial | partial | rack |
| CabinetView | Physical and spatial | partial | rack |
| SlotView | Physical and spatial | partial | — |
| EquipmentModuleLayout | Physical and spatial | planned | — |
| ChamberLayout | Physical and spatial | planned | — |
| FloorPlan | Physical and spatial | partial | floorplan |
| FabBayLayout | Physical and spatial | partial | floorplan |
| GridMap | Physical and spatial | planned | — |
| ZoneMap | Physical and spatial | planned | — |
| GenericSpaceAllocator | Physical and spatial | planned | — |
| CoordinateCanvas | Physical and spatial | planned | — |
| ImageAnnotation | Physical and spatial | planned | — |
| RegionAnnotation | Physical and spatial | planned | — |
| HotspotOverlay | Physical and spatial | planned | — |
| SpatialHeatmap | Physical and spatial | planned | — |
| PortMap | Physical and spatial | partial | — |
| ConnectorMap | Physical and spatial | partial | — |
| WaferMap | Semiconductor wafer and substrate | partial | wafer |
| WaferBinMap | Semiconductor wafer and substrate | partial | wafer |
| DefectMap | Semiconductor wafer and substrate | partial | — |
| DefectDensityMap | Semiconductor wafer and substrate | partial | — |
| WaferSelectionMap | Semiconductor wafer and substrate | partial | wafer |
| WaferComparison | Semiconductor wafer and substrate | planned | — |
| WaferZoneOverlay | Semiconductor wafer and substrate | partial | — |
| EdgeExclusionOverlay | Semiconductor wafer and substrate | planned | — |
| ReticleFieldOverlay | Semiconductor wafer and substrate | planned | — |
| DieGrid | Semiconductor wafer and substrate | partial | wafer |
| WaferSlotMap | Semiconductor wafer and substrate | partial | carrier |
| CarrierSlotMap | Semiconductor wafer and substrate | partial | carrier |
| FOUPView | Semiconductor wafer and substrate | partial | carrier |
| SubstrateTrackingTimeline | Semiconductor wafer and substrate | planned | — |
| LotTraveler | Semiconductor lot and process | partial | traveler |
| LotGenealogy | Semiconductor lot and process | planned | — |
| LotHistory | Semiconductor lot and process | partial | — |
| ProcessRoute | Semiconductor lot and process | partial | — |
| ProcessStepTimeline | Semiconductor lot and process | partial | traveler |
| WIPByStep | Semiconductor lot and process | partial | — |
| WIPHeatmap | Semiconductor lot and process | planned | — |
| HoldQueue | Semiconductor lot and process | planned | — |
| ReworkFlow | Semiconductor lot and process | planned | — |
| DispatchQueue | Semiconductor lot and process | planned | — |
| CycleTimeChart | Semiconductor lot and process | planned | — |
| QueueTimeChart | Semiconductor lot and process | planned | — |
| BottleneckView | Semiconductor lot and process | planned | — |
| ControlJobView | Semiconductor lot and process | planned | — |
| ProcessJobView | Semiconductor lot and process | planned | — |
| RecipeEditor | Semiconductor recipes | partial | — |
| RecipeParameterGrid | Semiconductor recipes | partial | — |
| RecipeDiff | Semiconductor recipes | partial | diff |
| RecipeVersionHistory | Semiconductor recipes | partial | — |
| ProcessWindow | Semiconductor recipes | partial | — |
| ParameterLimits | Semiconductor recipes | partial | — |
| GoldenRecipeComparison | Semiconductor recipes | partial | — |
| APCStatus | Semiconductor recipes | planned | — |
| RunToRunAdjustmentHistory | Semiconductor recipes | planned | — |
| EquipmentStatePanel | Semiconductor equipment | partial | — |
| EquipmentStateTimeline | Semiconductor equipment | partial | timeline |
| ModuleStatePanel | Semiconductor equipment | partial | — |
| ChamberStatePanel | Semiconductor equipment | partial | — |
| EquipmentStateStackChart | Semiconductor equipment | planned | — |
| AvailabilityPanel | Semiconductor equipment | partial | — |
| UtilizationPanel | Semiconductor equipment | partial | — |
| MTBF | Semiconductor equipment | partial | — |
| MTTR | Semiconductor equipment | partial | — |
| OEEPanel | Semiconductor equipment | planned | — |
| AlarmConsole | Semiconductor equipment | planned | — |
| AlarmTimeline | Semiconductor equipment | partial | — |
| EquipmentHealthMatrix | Semiconductor equipment | planned | — |
| PMCalendar | Semiconductor equipment | planned | — |
| MaintenanceTimeline | Semiconductor equipment | partial | — |
| EquipmentModuleDiagram | Semiconductor equipment | planned | — |
| ChamberMatching | Semiconductor equipment | planned | — |
| ToolComparison | Semiconductor equipment | planned | — |
| SPCDashboard | Semiconductor analytics | partial | — |
| ControlChartSuite | Semiconductor analytics | partial | — |
| FDCTraceViewer | Semiconductor analytics | planned | — |
| TraceOverlay | Semiconductor analytics | planned | — |
| ParameterTrend | Semiconductor analytics | partial | process |
| YieldTrend | Semiconductor analytics | planned | — |
| YieldByLot | Semiconductor analytics | planned | — |
| YieldByTool | Semiconductor analytics | planned | — |
| YieldByRecipe | Semiconductor analytics | planned | — |
| ParetoDefect | Semiconductor analytics | partial | — |
| BinPareto | Semiconductor analytics | planned | — |
| CapabilityAnalysis | Semiconductor analytics | partial | — |
| FabOverview | Semiconductor factory | planned | — |
| BayMap | Semiconductor factory | planned | — |
| ToolMap | Semiconductor factory | planned | — |
| CapacityDashboard | Semiconductor factory | planned | — |
| ConstraintDashboard | Semiconductor factory | planned | — |
| WIPDashboard | Semiconductor factory | planned | — |
| ProductionFlow | Semiconductor factory | planned | — |
| ShiftDashboard | Semiconductor factory | planned | — |
| Backlog | Software planning | planned | — |
| IssueTable | Software planning | planned | — |
| KanbanBoard | Software planning | partial | boards |
| SprintBoard | Software planning | planned | — |
| SprintOverview | Software planning | planned | — |
| Milestones | Software planning | partial | — |
| ReleasePlan | Software planning | partial | — |
| RepositoryTree | Software code and documentation | planned | — |
| FileTree | Software code and documentation | partial | split |
| CodeViewer | Software code and documentation | planned | — |
| DiffViewer | Software code and documentation | planned | — |
| SplitDiff | Software code and documentation | partial | diff |
| UnifiedDiff | Software code and documentation | planned | — |
| JSONViewer | Software code and documentation | partial | json |
| YAMLViewer | Software code and documentation | planned | — |
| MarkdownViewer | Software code and documentation | partial | — |
| PipelineGraph | Software delivery | partial | pipeline |
| JobGraph | Software delivery | partial | — |
| BuildTimeline | Software delivery | partial | — |
| DeploymentTimeline | Software delivery | partial | — |
| EnvironmentMatrix | Software delivery | planned | — |
| ReleaseDashboard | Software delivery | partial | — |
| ArtifactBrowser | Software delivery | planned | — |
| MetricsExplorer | Software operations | partial | — |
| LogExplorer | Software operations | partial | logs |
| TraceExplorer | Software operations | partial | traces |
| TraceWaterfall | Software operations | partial | traces |
| IncidentCommandCenter | Software operations | partial | — |
| AlertConsole | Software operations | partial | — |
| SLODashboard | Software operations | partial | — |
| ErrorBudget | Software operations | partial | — |
| OnCallSchedule | Software operations | planned | — |
| RunbookViewer | Software operations | partial | — |
| APIExplorer | Software platform and integrations | planned | — |
| RequestBuilder | Software platform and integrations | planned | — |
| ResponseViewer | Software platform and integrations | planned | — |
| WebhookInspector | Software platform and integrations | planned | — |
| EventViewer | Software platform and integrations | planned | — |
| QueueInspector | Software platform and integrations | planned | — |
| JobScheduler | Software platform and integrations | planned | — |
| FeatureFlagConsole | Software platform and integrations | planned | — |
| ConfigurationViewer | Software platform and integrations | partial | json |
| ConfigurationDiff | Software platform and integrations | partial | diff |
| AuditViewer | Software platform and integrations | planned | — |
| PlainTextEditor | Editors and documents | planned | — |
| StreamingLogViewer | Editors and documents | planned | — |
| TerminalOutput | Editors and documents | planned | — |
| FileBrowser | Editors and documents | planned | — |
| DirectoryTree | Editors and documents | planned | — |
| AttachmentGallery | Editors and documents | partial | — |
| ImageViewer | Editors and documents | planned | — |
| ImageAnnotator | Editors and documents | planned | — |
| DocumentMetadata | Editors and documents | planned | — |
| PropertyInspector | Editors and documents | planned | — |
| SchemaViewer | Editors and documents | planned | — |
| APIResponseInspector | Editors and documents | planned | — |
| ObjectInspector | Editors and documents | planned | — |
| Comments | Collaboration and workflow | planned | — |
| ThreadedComments | Collaboration and workflow | planned | — |
| Mentions | Collaboration and workflow | planned | — |
| ActivityFeed | Collaboration and workflow | planned | — |
| AuditTimeline | Collaboration and workflow | planned | — |
| ApprovalPanel | Collaboration and workflow | planned | — |
| ApprovalFlow | Collaboration and workflow | planned | — |
| Assignment | Collaboration and workflow | planned | — |
| OwnerPicker | Collaboration and workflow | planned | — |
| TeamPicker | Collaboration and workflow | planned | — |
| Watchers | Collaboration and workflow | planned | — |
| Followers | Collaboration and workflow | planned | — |
| Labels | Collaboration and workflow | planned | — |
| Checklist | Collaboration and workflow | planned | — |
| TaskList | Collaboration and workflow | planned | — |
| StatusTransition | Collaboration and workflow | planned | — |
| WorkflowStepper | Collaboration and workflow | planned | — |
| Escalation | Collaboration and workflow | planned | — |
| NotificationPreferences | Collaboration and workflow | partial | — |
| Presence | Collaboration and workflow | planned | — |
| ConflictResolution | Collaboration and workflow | planned | — |
| RevisionHistory | Collaboration and workflow | planned | — |
| UserDirectory | Administration | partial | — |
| MemberTable | Administration | partial | — |
| RoleManager | Administration | partial | — |
| PermissionMatrix | Administration | partial | permissions |
| TenantSelector | Administration | partial | — |
| TenantAdministration | Administration | planned | — |
| FeatureFlagManager | Administration | partial | — |
| Settings | Administration | planned | — |
| Preferences | Administration | partial | — |
| ThemeSettings | Administration | partial | — |
| AuditConsole | Administration | partial | — |
| HealthDashboard | Administration | partial | — |
| RuntimeDiagnostics | Administration | partial | — |
| StorageDiagnostics | Administration | planned | — |
| APIConnectivity | Administration | partial | — |
| EnvironmentInfo | Administration | partial | — |
| AppShell | Layouts | partial | — |
| SidebarShell | Layouts | partial | — |
| TopNavShell | Layouts | planned | — |
| DualSidebarShell | Layouts | planned | — |
| HeaderContent | Layouts | partial | — |
| HeaderToolbarContent | Layouts | partial | — |
| SingleColumn | Layouts | planned | — |
| TwoColumn | Layouts | planned | — |
| ThreeColumn | Layouts | planned | — |
| DashboardGrid | Layouts | partial | — |
| MasterDetail | Layouts | partial | — |
| SplitHorizontal | Layouts | partial | — |
| SplitVertical | Layouts | partial | — |
| ResizableSplit | Layouts | partial | — |
| InspectorLayout | Layouts | partial | — |
| StickyHeader | Layouts | planned | — |
| StickyFooter | Layouts | planned | — |
| StickySidebar | Layouts | planned | — |
| FullHeightWorkspace | Layouts | partial | — |
| CanvasWorkspace | Layouts | partial | — |
| DenseOperationsWorkspace | Layouts | partial | — |
| CenteredForm | Layouts | planned | — |
| DossierLayout | Layouts | planned | — |
| ResponsiveCards | Layouts | planned | — |
| AccessKeyIdentity | Platform services | partial | — |
| TenantIsolation | Platform services | partial | — |
| Authorization | Platform services | partial | — |
| ServerPagination | Platform services | planned | — |
| GeneratedAPIContracts | Platform services | partial | — |
| Transactions | Platform services | partial | — |
| MigrationHistory | Platform services | partial | — |
| ConfigDatabaseMigrations | Platform services | partial | — |
| AttachmentsProtection | Platform services | partial | — |
| Idempotency | Platform services | partial | — |
| OptimisticConcurrency | Platform services | planned | — |
| AuditPersistence | Platform services | partial | — |
| BackupManifest | Platform services | partial | — |
| IsolatedRestore | Platform services | partial | — |
| MigrationRehearsal | Platform services | partial | — |
| DirectDatabaseSDK | Platform services | partial | — |
| ImportPreview | Platform services | planned | — |
| CSVExchange | Platform services | planned | — |
| XLSXExchange | Platform services | planned | — |
| RevisionRevert | Platform services | partial | — |
| SavedViewsPersistence | Platform services | partial | — |
| DurableJobs | Platform services | partial | — |
| WebhooksOutbound | Platform services | partial | — |
| WebhooksInbound | Platform services | planned | — |
| RealtimeBus | Platform services | partial | — |
| IntegrationCredentials | Platform services | partial | — |
| RateLimits | Platform services | partial | — |
| HealthReadiness | Platform services | planned | — |
| StructuredLogging | Platform services | partial | — |
| OTelMetrics | Platform services | planned | — |
| OTelTraces | Platform services | planned | — |
| NotificationDelivery | Platform services | partial | — |
| ApplicationGenerator | Platform services | partial | — |
| WorkspaceGenerator | Platform services | partial | — |
| UpgradePlanner | Platform services | partial | — |
| UpgradeApply | Platform services | partial | — |
| UpgradeRollback | Platform services | partial | — |
| ExperienceLab | Developer and certification | partial | — |
| Storybook | Developer and certification | planned | — |
| ThemeStudio | Developer and certification | partial | — |
| ArchitectureRules | Developer and certification | partial | — |
| DependencyLocks | Developer and certification | planned | — |
| SecretScanning | Developer and certification | partial | — |
| AdvisoryScanning | Developer and certification | planned | — |
| SAST | Developer and certification | planned | — |
| SBOM | Developer and certification | planned | — |
| Provenance | Developer and certification | planned | — |
| CleanMacSetup | Developer and certification | planned | — |
| CorporatePaaSPublish | Developer and certification | planned | — |
| CorporateStorageQualification | Developer and certification | planned | — |
| CorporateIdentityQualification | Developer and certification | planned | — |
| VisualRegression | Developer and certification | planned | — |
| KeyboardRegression | Developer and certification | planned | — |
| AccessibilityAssessment | Developer and certification | planned | — |
| PerformanceBudgets | Developer and certification | partial | — |
| SourceCheckpoints | Developer and certification | partial | — |
| CatalogCompleteness | Developer and certification | partial | — |
| APIContractDrift | Developer and certification | partial | — |
| DocumentationChecks | Developer and certification | planned | — |
