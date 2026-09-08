# Component and platform coverage

This is an explicit delivery ledger, not a percentage-complete claim. The first table describes the standalone Experience Lab native demonstration families. The retained catalog table below describes the generic React/platform family registry; a stable generic variant is not a claim that every specialized domain workflow is production-qualified.

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
| Heading | Typography and content | stable | catalog-variant-gallery |
| Subheading | Typography and content | stable | catalog-variant-gallery |
| BodyText | Typography and content | stable | catalog-variant-gallery |
| SecondaryText | Typography and content | stable | catalog-variant-gallery |
| Caption | Typography and content | stable | catalog-variant-gallery |
| Label | Typography and content | stable | catalog-variant-gallery |
| MonoText | Typography and content | stable | catalog-variant-gallery |
| InlineCode | Typography and content | stable | catalog-variant-gallery |
| CodeBlock | Typography and content | stable | catalog-variant-gallery |
| Link | Typography and content | stable | catalog-variant-gallery |
| ExternalLink | Typography and content | stable | catalog-variant-gallery |
| TruncatedText | Typography and content | stable | catalog-variant-gallery |
| ExpandableText | Typography and content | stable | catalog-variant-gallery |
| CopyableText | Typography and content | stable | catalog-variant-gallery |
| KeyValue | Typography and content | stable | catalog-variant-gallery |
| DefinitionList | Typography and content | stable | catalog-variant-gallery |
| MetricValue | Typography and content | stable | catalog-variant-gallery |
| MetricDelta | Typography and content | stable | catalog-variant-gallery |
| Timestamp | Typography and content | stable | catalog-variant-gallery |
| RelativeTime | Typography and content | stable | catalog-variant-gallery |
| Duration | Typography and content | stable | catalog-variant-gallery |
| UserIdentity | Typography and content | stable | catalog-variant-gallery |
| EmptyValue | Typography and content | stable | catalog-variant-gallery |
| Button | Controls | stable | catalog-variant-gallery |
| IconButton | Controls | stable | catalog-variant-gallery |
| SplitButton | Controls | stable | catalog-variant-gallery |
| ButtonGroup | Controls | stable | catalog-variant-gallery |
| ToggleButton | Controls | stable | catalog-variant-gallery |
| ToggleGroup | Controls | stable | catalog-variant-gallery |
| SegmentedControl | Controls | stable | catalog-variant-gallery |
| Checkbox | Controls | stable | catalog-variant-gallery |
| Radio | Controls | stable | catalog-variant-gallery |
| Switch | Controls | stable | catalog-variant-gallery |
| Slider | Controls | stable | catalog-variant-gallery |
| RangeSlider | Controls | stable | catalog-variant-gallery |
| LinkButton | Controls | stable | catalog-variant-gallery |
| CopyButton | Controls | stable | catalog-variant-gallery |
| FavoriteButton | Controls | stable | catalog-variant-gallery |
| PinButton | Controls | stable | catalog-variant-gallery |
| RefreshButton | Controls | stable | catalog-variant-gallery |
| Badge | Indicators | stable | catalog-variant-gallery |
| StatusBadge | Indicators | stable | catalog-variant-gallery |
| StatusDot | Indicators | stable | catalog-variant-gallery |
| Chip | Indicators | stable | catalog-variant-gallery |
| Tag | Indicators | stable | catalog-variant-gallery |
| CountBadge | Indicators | stable | catalog-variant-gallery |
| Avatar | Indicators | stable | catalog-variant-gallery |
| AvatarGroup | Indicators | stable | catalog-variant-gallery |
| PresenceIndicator | Indicators | stable | catalog-variant-gallery |
| ProgressBar | Indicators | stable | catalog-variant-gallery |
| ProgressRing | Indicators | stable | catalog-variant-gallery |
| Spinner | Indicators | stable | catalog-variant-gallery |
| Skeleton | Indicators | stable | catalog-variant-gallery |
| HealthIndicator | Indicators | stable | catalog-variant-gallery |
| TrendIndicator | Indicators | stable | catalog-variant-gallery |
| SeverityIndicator | Indicators | stable | catalog-variant-gallery |
| SLAIndicator | Indicators | stable | catalog-variant-gallery |
| Modal | Windows and overlays | stable | catalog-variant-gallery, windows |
| AlertDialog | Windows and overlays | stable | catalog-variant-gallery |
| ConfirmDialog | Windows and overlays | stable | catalog-variant-gallery, windows |
| DestructiveConfirmDialog | Windows and overlays | stable | catalog-variant-gallery |
| FormDialog | Windows and overlays | stable | catalog-variant-gallery, windows |
| WizardDialog | Windows and overlays | stable | catalog-variant-gallery, windows |
| DossierDialog | Windows and overlays | stable | catalog-variant-gallery |
| ComparisonDialog | Windows and overlays | stable | catalog-variant-gallery |
| FullScreenDialog | Windows and overlays | stable | catalog-variant-gallery, windows |
| DrawerLeft | Windows and overlays | stable | catalog-variant-gallery |
| DrawerRight | Windows and overlays | stable | catalog-variant-gallery, windows |
| DrawerBottom | Windows and overlays | stable | catalog-variant-gallery |
| InspectorDrawer | Windows and overlays | stable | catalog-variant-gallery, windows |
| DetailsDrawer | Windows and overlays | stable | catalog-variant-gallery |
| Popover | Windows and overlays | stable | catalog-variant-gallery, windows |
| Dropdown | Windows and overlays | stable | catalog-variant-gallery |
| ComboDropdown | Windows and overlays | stable | catalog-variant-gallery |
| HoverCard | Windows and overlays | stable | catalog-variant-gallery |
| Tooltip | Windows and overlays | stable | catalog-variant-gallery, windows |
| ContextMenu | Windows and overlays | stable | catalog-variant-gallery |
| Menu | Windows and overlays | stable | catalog-variant-gallery |
| Submenu | Windows and overlays | stable | catalog-variant-gallery |
| ActionMenu | Windows and overlays | stable | catalog-variant-gallery |
| AnchoredFlyout | Windows and overlays | stable | catalog-variant-gallery |
| FloatingPanel | Windows and overlays | stable | catalog-variant-gallery |
| CommandPalette | Windows and overlays | stable | catalog-variant-gallery |
| SearchPalette | Windows and overlays | stable | catalog-variant-gallery |
| QuickSwitcher | Windows and overlays | stable | catalog-variant-gallery |
| Toast | Windows and overlays | stable | catalog-variant-gallery, windows |
| ToastStack | Windows and overlays | stable | catalog-variant-gallery, windows |
| NotificationCenter | Windows and overlays | stable | catalog-variant-gallery, notifications |
| NotificationDrawer | Windows and overlays | stable | catalog-variant-gallery |
| Banner | Windows and overlays | stable | catalog-variant-gallery |
| InlineAlert | Windows and overlays | stable | catalog-variant-gallery |
| BottomSheet | Windows and overlays | stable | catalog-variant-gallery, windows |
| SideSheet | Windows and overlays | stable | catalog-variant-gallery |
| MasterDetailPane | Windows and overlays | stable | catalog-variant-gallery, split |
| SplitPane | Windows and overlays | stable | catalog-variant-gallery, split |
| ResizablePane | Windows and overlays | stable | catalog-variant-gallery, split |
| SidecarPanel | Windows and overlays | stable | catalog-variant-gallery |
| DockedPanel | Windows and overlays | stable | catalog-variant-gallery |
| CollapsiblePanel | Windows and overlays | stable | catalog-variant-gallery |
| FloatingInspector | Windows and overlays | stable | catalog-variant-gallery |
| DockWorkspace | Windows and overlays | stable | catalog-variant-gallery |
| TextInput | Forms and inputs | stable | catalog-variant-gallery |
| Textarea | Forms and inputs | stable | catalog-variant-gallery |
| PasswordInput | Forms and inputs | stable | catalog-variant-gallery |
| SearchInput | Forms and inputs | stable | catalog-variant-gallery |
| IntegerInput | Forms and inputs | stable | catalog-variant-gallery |
| DecimalInput | Forms and inputs | stable | catalog-variant-gallery |
| ScientificNumberInput | Forms and inputs | stable | catalog-variant-gallery |
| CurrencyInput | Forms and inputs | stable | catalog-variant-gallery |
| PercentInput | Forms and inputs | stable | catalog-variant-gallery |
| UnitAwareNumberInput | Forms and inputs | stable | catalog-variant-gallery |
| EmailInput | Forms and inputs | stable | catalog-variant-gallery |
| PhoneInput | Forms and inputs | stable | catalog-variant-gallery |
| URLInput | Forms and inputs | stable | catalog-variant-gallery |
| Select | Forms and inputs | stable | catalog-variant-gallery |
| MultiSelect | Forms and inputs | stable | catalog-variant-gallery |
| Combobox | Forms and inputs | stable | catalog-variant-gallery |
| Autocomplete | Forms and inputs | stable | catalog-variant-gallery |
| TagInput | Forms and inputs | stable | catalog-variant-gallery |
| TokenInput | Forms and inputs | stable | catalog-variant-gallery |
| SearchableSelector | Forms and inputs | stable | catalog-variant-gallery |
| CheckboxGroup | Forms and inputs | stable | catalog-variant-gallery |
| RadioGroup | Forms and inputs | stable | catalog-variant-gallery |
| DatePicker | Forms and inputs | stable | catalog-variant-gallery |
| TimePicker | Forms and inputs | stable | catalog-variant-gallery |
| DateTimePicker | Forms and inputs | stable | catalog-variant-gallery |
| DateRangePicker | Forms and inputs | stable | catalog-variant-gallery |
| MonthPicker | Forms and inputs | stable | catalog-variant-gallery |
| YearPicker | Forms and inputs | stable | catalog-variant-gallery |
| DurationInput | Forms and inputs | stable | catalog-variant-gallery |
| TimezonePicker | Forms and inputs | stable | catalog-variant-gallery |
| FileInput | Forms and inputs | stable | catalog-variant-gallery |
| MultiFileUpload | Forms and inputs | stable | catalog-variant-gallery |
| DragDropUpload | Forms and inputs | stable | catalog-variant-gallery |
| ImageUpload | Forms and inputs | stable | catalog-variant-gallery |
| ColorPicker | Forms and inputs | stable | catalog-variant-gallery |
| IconPicker | Forms and inputs | stable | catalog-variant-gallery |
| KeyValueEditor | Forms and inputs | stable | catalog-variant-gallery |
| ArrayEditor | Forms and inputs | stable | catalog-variant-gallery |
| ObjectEditor | Forms and inputs | stable | catalog-variant-gallery |
| JSONEditor | Forms and inputs | stable | catalog-variant-gallery, json |
| YAMLEditor | Forms and inputs | stable | catalog-variant-gallery |
| CodeEditor | Forms and inputs | stable | catalog-variant-gallery |
| MarkdownEditor | Forms and inputs | stable | catalog-variant-gallery |
| RichTextEditor | Forms and inputs | stable | catalog-variant-gallery |
| CronBuilder | Forms and inputs | stable | catalog-variant-gallery |
| ExpressionBuilder | Forms and inputs | stable | catalog-variant-gallery |
| FilterBuilder | Forms and inputs | stable | catalog-variant-gallery |
| QueryBuilder | Forms and inputs | stable | catalog-variant-gallery |
| RuleBuilder | Forms and inputs | stable | catalog-variant-gallery |
| FormulaBuilder | Forms and inputs | stable | catalog-variant-gallery |
| CoordinateInput | Forms and inputs | stable | catalog-variant-gallery |
| RangeInput | Forms and inputs | stable | catalog-variant-gallery |
| ToleranceInput | Forms and inputs | stable | catalog-variant-gallery, forms |
| EngineeringUnitInput | Forms and inputs | stable | catalog-variant-gallery, forms |
| DynamicSchemaForm | Forms and inputs | stable | catalog-variant-gallery |
| TabbedForm | Forms and inputs | stable | catalog-variant-gallery |
| SectionedForm | Forms and inputs | stable | catalog-variant-gallery, forms |
| WizardForm | Forms and inputs | stable | catalog-variant-gallery |
| InlineEditableForm | Forms and inputs | stable | catalog-variant-gallery |
| BulkEditForm | Forms and inputs | stable | catalog-variant-gallery |
| SimpleTable | Tables and grids | stable | catalog-variant-gallery, tables |
| DataGrid | Tables and grids | stable | catalog-variant-gallery, tables |
| VirtualizedGrid | Tables and grids | stable | catalog-variant-gallery |
| EditableGrid | Tables and grids | stable | catalog-variant-gallery |
| InlineEditGrid | Tables and grids | stable | catalog-variant-gallery |
| ServerSideGrid | Tables and grids | stable | catalog-variant-gallery |
| InfiniteGrid | Tables and grids | stable | catalog-variant-gallery |
| GroupedGrid | Tables and grids | stable | catalog-variant-gallery, tables |
| TreeGrid | Tables and grids | stable | catalog-variant-gallery |
| PivotGrid | Tables and grids | stable | catalog-variant-gallery |
| CrossTabGrid | Tables and grids | stable | catalog-variant-gallery |
| MasterDetailGrid | Tables and grids | stable | catalog-variant-gallery |
| NestedGrid | Tables and grids | stable | catalog-variant-gallery |
| ComparisonGrid | Tables and grids | stable | catalog-variant-gallery |
| DiffGrid | Tables and grids | stable | catalog-variant-gallery |
| MatrixGrid | Tables and grids | stable | catalog-variant-gallery |
| PropertyGrid | Tables and grids | stable | catalog-variant-gallery |
| LogGrid | Tables and grids | stable | catalog-variant-gallery |
| EventGrid | Tables and grids | stable | catalog-variant-gallery |
| MetricGrid | Tables and grids | stable | catalog-variant-gallery |
| SelectableGrid | Tables and grids | stable | catalog-variant-gallery, tables |
| RangeSelectableGrid | Tables and grids | stable | catalog-variant-gallery |
| BulkActionGrid | Tables and grids | stable | catalog-variant-gallery, tables |
| ContextMenuGrid | Tables and grids | stable | catalog-variant-gallery |
| PinnedColumnGrid | Tables and grids | stable | catalog-variant-gallery |
| PinnedRowGrid | Tables and grids | stable | catalog-variant-gallery |
| SummaryRowGrid | Tables and grids | stable | catalog-variant-gallery |
| CalculatedColumnGrid | Tables and grids | stable | catalog-variant-gallery |
| FormulaColumnGrid | Tables and grids | stable | catalog-variant-gallery |
| TableWorkspace | Workspace archetypes | stable | catalog-variant-gallery, tables |
| BoardWorkspace | Workspace archetypes | stable | boards, catalog-variant-gallery |
| DashboardWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| FormWorkspace | Workspace archetypes | stable | catalog-variant-gallery, forms |
| DetailWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| MasterDetailWorkspace | Workspace archetypes | stable | catalog-variant-gallery, split |
| SplitViewWorkspace | Workspace archetypes | stable | catalog-variant-gallery, split |
| TimelineWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| GanttWorkspace | Workspace archetypes | stable | catalog-variant-gallery, gantt |
| CalendarWorkspace | Workspace archetypes | stable | calendar, catalog-variant-gallery |
| SchedulerWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| KanbanWorkspace | Workspace archetypes | stable | boards, catalog-variant-gallery |
| TreeWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| HierarchyWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| DiagramWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| TopologyWorkspace | Workspace archetypes | stable | catalog-variant-gallery, topology |
| ProcessFlowWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| MapWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| FloorPlanWorkspace | Workspace archetypes | stable | catalog-variant-gallery, floorplan |
| RackWorkspace | Workspace archetypes | stable | catalog-variant-gallery, rack |
| AnalyticalWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| SPCWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| WaferWorkspace | Workspace archetypes | stable | catalog-variant-gallery, wafer |
| LogWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| IncidentWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| ComparisonWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| InvestigationWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| DocumentationWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| CodeWorkspace | Workspace archetypes | stable | catalog-variant-gallery |
| Line | Charts and visualizations | stable | catalog-variant-gallery, process |
| MultiLine | Charts and visualizations | stable | catalog-variant-gallery |
| Area | Charts and visualizations | stable | catalog-variant-gallery, process |
| StackedArea | Charts and visualizations | stable | catalog-variant-gallery |
| Bar | Charts and visualizations | stable | catalog-variant-gallery, process |
| GroupedBar | Charts and visualizations | stable | catalog-variant-gallery |
| StackedBar | Charts and visualizations | stable | catalog-variant-gallery |
| HorizontalBar | Charts and visualizations | stable | catalog-variant-gallery, charts |
| ComboChart | Charts and visualizations | stable | catalog-variant-gallery |
| Scatter | Charts and visualizations | stable | catalog-variant-gallery, process |
| Bubble | Charts and visualizations | stable | catalog-variant-gallery |
| JitterScatter | Charts and visualizations | stable | catalog-variant-gallery |
| Histogram | Charts and visualizations | stable | catalog-variant-gallery |
| BoxPlot | Charts and visualizations | stable | catalog-variant-gallery |
| Violin | Charts and visualizations | stable | catalog-variant-gallery |
| Beeswarm | Charts and visualizations | stable | catalog-variant-gallery |
| Pie | Charts and visualizations | stable | catalog-variant-gallery |
| Donut | Charts and visualizations | stable | catalog-variant-gallery, charts |
| Pareto | Charts and visualizations | stable | catalog-variant-gallery |
| Waterfall | Charts and visualizations | stable | catalog-variant-gallery |
| Funnel | Charts and visualizations | stable | catalog-variant-gallery |
| Gauge | Charts and visualizations | stable | catalog-variant-gallery |
| Bullet | Charts and visualizations | stable | catalog-variant-gallery |
| ProgressGauge | Charts and visualizations | stable | catalog-variant-gallery |
| Radar | Charts and visualizations | stable | catalog-variant-gallery |
| Heatmap | Charts and visualizations | stable | catalog-variant-gallery, charts |
| CalendarHeatmap | Charts and visualizations | stable | catalog-variant-gallery |
| Treemap | Charts and visualizations | stable | catalog-variant-gallery |
| Sunburst | Charts and visualizations | stable | catalog-variant-gallery |
| Sankey | Charts and visualizations | stable | catalog-variant-gallery |
| Chord | Charts and visualizations | stable | catalog-variant-gallery |
| ParallelCoordinates | Charts and visualizations | stable | catalog-variant-gallery |
| GraphChart | Charts and visualizations | stable | catalog-variant-gallery |
| NetworkGraph | Charts and visualizations | stable | catalog-variant-gallery, topology |
| RangeChart | Charts and visualizations | stable | catalog-variant-gallery |
| ConfidenceBandChart | Charts and visualizations | stable | catalog-variant-gallery |
| Sparkline | Charts and visualizations | stable | catalog-variant-gallery |
| MicroBar | Charts and visualizations | stable | catalog-variant-gallery |
| MiniTrend | Charts and visualizations | stable | catalog-variant-gallery |
| RunChart | Statistical process engineering | stable | catalog-variant-gallery |
| XbarRChart | Statistical process engineering | stable | catalog-variant-gallery |
| XbarSChart | Statistical process engineering | stable | catalog-variant-gallery |
| IndividualsMovingRange | Statistical process engineering | stable | catalog-variant-gallery |
| PChart | Statistical process engineering | stable | catalog-variant-gallery |
| NPChart | Statistical process engineering | stable | catalog-variant-gallery |
| CChart | Statistical process engineering | stable | catalog-variant-gallery |
| UChart | Statistical process engineering | stable | catalog-variant-gallery |
| CUSUMChart | Statistical process engineering | stable | catalog-variant-gallery |
| EWMAChart | Statistical process engineering | stable | catalog-variant-gallery |
| ControlLimitsChart | Statistical process engineering | stable | catalog-variant-gallery, process |
| CapabilityHistogram | Statistical process engineering | stable | catalog-variant-gallery |
| CpCpkPanel | Statistical process engineering | stable | catalog-variant-gallery |
| PpPpkPanel | Statistical process engineering | stable | catalog-variant-gallery |
| DistributionComparison | Statistical process engineering | stable | catalog-variant-gallery |
| CorrelationMatrix | Statistical process engineering | stable | catalog-variant-gallery |
| ScatterMatrix | Statistical process engineering | stable | catalog-variant-gallery |
| RegressionPlot | Statistical process engineering | stable | catalog-variant-gallery |
| ResidualPlot | Statistical process engineering | stable | catalog-variant-gallery |
| ParetoDefects | Statistical process engineering | stable | catalog-variant-gallery |
| ProcessWindowChart | Statistical process engineering | stable | catalog-variant-gallery |
| ToleranceBandChart | Statistical process engineering | stable | catalog-variant-gallery |
| GoldenSampleComparison | Statistical process engineering | stable | catalog-variant-gallery |
| SimpleTimeline | Planning and time | stable | catalog-variant-gallery |
| VerticalTimeline | Planning and time | stable | catalog-variant-gallery |
| HorizontalTimeline | Planning and time | stable | catalog-variant-gallery |
| EventTimeline | Planning and time | stable | catalog-variant-gallery |
| IncidentTimeline | Planning and time | stable | catalog-variant-gallery |
| StateTimeline | Planning and time | stable | catalog-variant-gallery, timeline |
| MilestoneTimeline | Planning and time | stable | catalog-variant-gallery |
| GanttChart | Planning and time | stable | catalog-variant-gallery, gantt |
| DependencyGantt | Planning and time | stable | catalog-variant-gallery, gantt |
| ResourceGantt | Planning and time | stable | catalog-variant-gallery |
| PortfolioGantt | Planning and time | stable | catalog-variant-gallery |
| Roadmap | Planning and time | stable | catalog-variant-gallery |
| ResourceSchedule | Planning and time | stable | catalog-variant-gallery |
| MachineSchedule | Planning and time | stable | catalog-variant-gallery |
| PeopleSchedule | Planning and time | stable | catalog-variant-gallery |
| ShiftSchedule | Planning and time | stable | catalog-variant-gallery |
| Calendar | Planning and time | stable | calendar, catalog-variant-gallery |
| MonthCalendar | Planning and time | stable | calendar, catalog-variant-gallery |
| WeekCalendar | Planning and time | stable | catalog-variant-gallery |
| DayCalendar | Planning and time | stable | catalog-variant-gallery |
| Agenda | Planning and time | stable | catalog-variant-gallery |
| ResourceCalendar | Planning and time | stable | catalog-variant-gallery |
| SwimlaneTimeline | Planning and time | stable | catalog-variant-gallery |
| Burndown | Planning and time | stable | catalog-variant-gallery |
| Burnup | Planning and time | stable | catalog-variant-gallery |
| CumulativeFlow | Planning and time | stable | catalog-variant-gallery |
| CapacityTimeline | Planning and time | stable | catalog-variant-gallery |
| UtilizationTimeline | Planning and time | stable | catalog-variant-gallery |
| FlowDiagram | Diagrams and canvases | stable | catalog-variant-gallery |
| DependencyGraph | Diagrams and canvases | stable | catalog-variant-gallery, topology |
| ServiceTopology | Diagrams and canvases | stable | catalog-variant-gallery, topology |
| NetworkTopology | Diagrams and canvases | stable | catalog-variant-gallery |
| ArchitectureDiagram | Diagrams and canvases | stable | catalog-variant-gallery |
| ProcessFlow | Diagrams and canvases | stable | catalog-variant-gallery |
| ManufacturingRoute | Diagrams and canvases | stable | catalog-variant-gallery |
| DAG | Diagrams and canvases | stable | catalog-variant-gallery |
| WorkflowGraph | Diagrams and canvases | stable | catalog-variant-gallery |
| StateMachine | Diagrams and canvases | stable | catalog-variant-gallery |
| DecisionTree | Diagrams and canvases | stable | catalog-variant-gallery |
| OrgChart | Diagrams and canvases | stable | catalog-variant-gallery |
| GenealogyGraph | Diagrams and canvases | stable | catalog-variant-gallery |
| TraceabilityGraph | Diagrams and canvases | stable | catalog-variant-gallery |
| DataLineage | Diagrams and canvases | stable | catalog-variant-gallery |
| MindMap | Diagrams and canvases | stable | catalog-variant-gallery |
| SwimlaneDiagram | Diagrams and canvases | stable | catalog-variant-gallery |
| PortConnectionDiagram | Diagrams and canvases | stable | catalog-variant-gallery |
| NodeEditor | Diagrams and canvases | stable | catalog-variant-gallery |
| EdgeEditor | Diagrams and canvases | stable | catalog-variant-gallery |
| MiniMap | Diagrams and canvases | stable | catalog-variant-gallery |
| ZoomControls | Diagrams and canvases | stable | catalog-variant-gallery, topology |
| FitView | Diagrams and canvases | stable | catalog-variant-gallery, topology |
| SelectionBox | Diagrams and canvases | stable | catalog-variant-gallery |
| MultiSelectCanvas | Diagrams and canvases | stable | catalog-variant-gallery |
| RackElevation | Physical and spatial | stable | catalog-variant-gallery, rack |
| CabinetView | Physical and spatial | stable | catalog-variant-gallery, rack |
| SlotView | Physical and spatial | stable | catalog-variant-gallery |
| EquipmentModuleLayout | Physical and spatial | stable | catalog-variant-gallery |
| ChamberLayout | Physical and spatial | stable | catalog-variant-gallery |
| FloorPlan | Physical and spatial | stable | catalog-variant-gallery, floorplan |
| FabBayLayout | Physical and spatial | stable | catalog-variant-gallery, floorplan |
| GridMap | Physical and spatial | stable | catalog-variant-gallery |
| ZoneMap | Physical and spatial | stable | catalog-variant-gallery |
| GenericSpaceAllocator | Physical and spatial | stable | catalog-variant-gallery |
| CoordinateCanvas | Physical and spatial | stable | catalog-variant-gallery |
| ImageAnnotation | Physical and spatial | stable | catalog-variant-gallery |
| RegionAnnotation | Physical and spatial | stable | catalog-variant-gallery |
| HotspotOverlay | Physical and spatial | stable | catalog-variant-gallery |
| SpatialHeatmap | Physical and spatial | stable | catalog-variant-gallery |
| PortMap | Physical and spatial | stable | catalog-variant-gallery |
| ConnectorMap | Physical and spatial | stable | catalog-variant-gallery |
| WaferMap | Semiconductor wafer and substrate | stable | catalog-variant-gallery, wafer |
| WaferBinMap | Semiconductor wafer and substrate | stable | catalog-variant-gallery, wafer |
| DefectMap | Semiconductor wafer and substrate | stable | catalog-variant-gallery |
| DefectDensityMap | Semiconductor wafer and substrate | stable | catalog-variant-gallery |
| WaferSelectionMap | Semiconductor wafer and substrate | stable | catalog-variant-gallery, wafer |
| WaferComparison | Semiconductor wafer and substrate | stable | catalog-variant-gallery |
| WaferZoneOverlay | Semiconductor wafer and substrate | stable | catalog-variant-gallery |
| EdgeExclusionOverlay | Semiconductor wafer and substrate | stable | catalog-variant-gallery |
| ReticleFieldOverlay | Semiconductor wafer and substrate | stable | catalog-variant-gallery |
| DieGrid | Semiconductor wafer and substrate | stable | catalog-variant-gallery, wafer |
| WaferSlotMap | Semiconductor wafer and substrate | stable | carrier, catalog-variant-gallery |
| CarrierSlotMap | Semiconductor wafer and substrate | stable | carrier, catalog-variant-gallery |
| FOUPView | Semiconductor wafer and substrate | stable | carrier, catalog-variant-gallery |
| SubstrateTrackingTimeline | Semiconductor wafer and substrate | stable | catalog-variant-gallery |
| LotTraveler | Semiconductor lot and process | stable | catalog-variant-gallery, traveler |
| LotGenealogy | Semiconductor lot and process | stable | catalog-variant-gallery |
| LotHistory | Semiconductor lot and process | stable | catalog-variant-gallery |
| ProcessRoute | Semiconductor lot and process | stable | catalog-variant-gallery |
| ProcessStepTimeline | Semiconductor lot and process | stable | catalog-variant-gallery, traveler |
| WIPByStep | Semiconductor lot and process | stable | catalog-variant-gallery |
| WIPHeatmap | Semiconductor lot and process | stable | catalog-variant-gallery |
| HoldQueue | Semiconductor lot and process | stable | catalog-variant-gallery |
| ReworkFlow | Semiconductor lot and process | stable | catalog-variant-gallery |
| DispatchQueue | Semiconductor lot and process | stable | catalog-variant-gallery |
| CycleTimeChart | Semiconductor lot and process | stable | catalog-variant-gallery |
| QueueTimeChart | Semiconductor lot and process | stable | catalog-variant-gallery |
| BottleneckView | Semiconductor lot and process | stable | catalog-variant-gallery |
| ControlJobView | Semiconductor lot and process | stable | catalog-variant-gallery |
| ProcessJobView | Semiconductor lot and process | stable | catalog-variant-gallery |
| RecipeEditor | Semiconductor recipes | stable | catalog-variant-gallery |
| RecipeParameterGrid | Semiconductor recipes | stable | catalog-variant-gallery |
| RecipeDiff | Semiconductor recipes | stable | catalog-variant-gallery, diff |
| RecipeVersionHistory | Semiconductor recipes | stable | catalog-variant-gallery |
| ProcessWindow | Semiconductor recipes | stable | catalog-variant-gallery |
| ParameterLimits | Semiconductor recipes | stable | catalog-variant-gallery |
| GoldenRecipeComparison | Semiconductor recipes | stable | catalog-variant-gallery |
| APCStatus | Semiconductor recipes | stable | catalog-variant-gallery |
| RunToRunAdjustmentHistory | Semiconductor recipes | stable | catalog-variant-gallery |
| EquipmentStatePanel | Semiconductor equipment | stable | catalog-variant-gallery |
| EquipmentStateTimeline | Semiconductor equipment | stable | catalog-variant-gallery, timeline |
| ModuleStatePanel | Semiconductor equipment | stable | catalog-variant-gallery |
| ChamberStatePanel | Semiconductor equipment | stable | catalog-variant-gallery |
| EquipmentStateStackChart | Semiconductor equipment | stable | catalog-variant-gallery |
| AvailabilityPanel | Semiconductor equipment | stable | catalog-variant-gallery |
| UtilizationPanel | Semiconductor equipment | stable | catalog-variant-gallery |
| MTBF | Semiconductor equipment | stable | catalog-variant-gallery |
| MTTR | Semiconductor equipment | stable | catalog-variant-gallery |
| OEEPanel | Semiconductor equipment | stable | catalog-variant-gallery |
| AlarmConsole | Semiconductor equipment | stable | catalog-variant-gallery |
| AlarmTimeline | Semiconductor equipment | stable | catalog-variant-gallery |
| EquipmentHealthMatrix | Semiconductor equipment | stable | catalog-variant-gallery |
| PMCalendar | Semiconductor equipment | stable | catalog-variant-gallery |
| MaintenanceTimeline | Semiconductor equipment | stable | catalog-variant-gallery |
| EquipmentModuleDiagram | Semiconductor equipment | stable | catalog-variant-gallery |
| ChamberMatching | Semiconductor equipment | stable | catalog-variant-gallery |
| ToolComparison | Semiconductor equipment | stable | catalog-variant-gallery |
| SPCDashboard | Semiconductor analytics | stable | catalog-variant-gallery |
| ControlChartSuite | Semiconductor analytics | stable | catalog-variant-gallery |
| FDCTraceViewer | Semiconductor analytics | stable | catalog-variant-gallery |
| TraceOverlay | Semiconductor analytics | stable | catalog-variant-gallery |
| ParameterTrend | Semiconductor analytics | stable | catalog-variant-gallery, process |
| YieldTrend | Semiconductor analytics | stable | catalog-variant-gallery |
| YieldByLot | Semiconductor analytics | stable | catalog-variant-gallery |
| YieldByTool | Semiconductor analytics | stable | catalog-variant-gallery |
| YieldByRecipe | Semiconductor analytics | stable | catalog-variant-gallery |
| ParetoDefect | Semiconductor analytics | stable | catalog-variant-gallery |
| BinPareto | Semiconductor analytics | stable | catalog-variant-gallery |
| CapabilityAnalysis | Semiconductor analytics | stable | catalog-variant-gallery |
| FabOverview | Semiconductor factory | stable | catalog-variant-gallery |
| BayMap | Semiconductor factory | stable | catalog-variant-gallery |
| ToolMap | Semiconductor factory | stable | catalog-variant-gallery |
| CapacityDashboard | Semiconductor factory | stable | catalog-variant-gallery |
| ConstraintDashboard | Semiconductor factory | stable | catalog-variant-gallery |
| WIPDashboard | Semiconductor factory | stable | catalog-variant-gallery |
| ProductionFlow | Semiconductor factory | stable | catalog-variant-gallery |
| ShiftDashboard | Semiconductor factory | stable | catalog-variant-gallery |
| Backlog | Software planning | stable | catalog-variant-gallery |
| IssueTable | Software planning | stable | catalog-variant-gallery |
| KanbanBoard | Software planning | stable | boards, catalog-variant-gallery |
| SprintBoard | Software planning | stable | catalog-variant-gallery |
| SprintOverview | Software planning | stable | catalog-variant-gallery |
| Milestones | Software planning | stable | catalog-variant-gallery |
| ReleasePlan | Software planning | stable | catalog-variant-gallery |
| RepositoryTree | Software code and documentation | stable | catalog-variant-gallery |
| FileTree | Software code and documentation | stable | catalog-variant-gallery, split |
| CodeViewer | Software code and documentation | stable | catalog-variant-gallery |
| DiffViewer | Software code and documentation | stable | catalog-variant-gallery |
| SplitDiff | Software code and documentation | stable | catalog-variant-gallery, diff |
| UnifiedDiff | Software code and documentation | stable | catalog-variant-gallery |
| JSONViewer | Software code and documentation | stable | catalog-variant-gallery, json |
| YAMLViewer | Software code and documentation | stable | catalog-variant-gallery |
| MarkdownViewer | Software code and documentation | stable | catalog-variant-gallery |
| PipelineGraph | Software delivery | stable | catalog-variant-gallery, pipeline |
| JobGraph | Software delivery | stable | catalog-variant-gallery |
| BuildTimeline | Software delivery | stable | catalog-variant-gallery |
| DeploymentTimeline | Software delivery | stable | catalog-variant-gallery |
| EnvironmentMatrix | Software delivery | stable | catalog-variant-gallery |
| ReleaseDashboard | Software delivery | stable | catalog-variant-gallery |
| ArtifactBrowser | Software delivery | stable | catalog-variant-gallery |
| MetricsExplorer | Software operations | stable | catalog-variant-gallery |
| LogExplorer | Software operations | stable | catalog-variant-gallery, logs |
| TraceExplorer | Software operations | stable | catalog-variant-gallery, traces |
| TraceWaterfall | Software operations | stable | catalog-variant-gallery, traces |
| IncidentCommandCenter | Software operations | stable | catalog-variant-gallery |
| AlertConsole | Software operations | stable | catalog-variant-gallery |
| SLODashboard | Software operations | stable | catalog-variant-gallery |
| ErrorBudget | Software operations | stable | catalog-variant-gallery |
| OnCallSchedule | Software operations | stable | catalog-variant-gallery |
| RunbookViewer | Software operations | stable | catalog-variant-gallery |
| APIExplorer | Software platform and integrations | stable | catalog-variant-gallery |
| RequestBuilder | Software platform and integrations | stable | catalog-variant-gallery |
| ResponseViewer | Software platform and integrations | stable | catalog-variant-gallery |
| WebhookInspector | Software platform and integrations | stable | catalog-variant-gallery |
| EventViewer | Software platform and integrations | stable | catalog-variant-gallery |
| QueueInspector | Software platform and integrations | stable | catalog-variant-gallery |
| JobScheduler | Software platform and integrations | stable | catalog-variant-gallery |
| FeatureFlagConsole | Software platform and integrations | stable | catalog-variant-gallery |
| ConfigurationViewer | Software platform and integrations | stable | catalog-variant-gallery, json |
| ConfigurationDiff | Software platform and integrations | stable | catalog-variant-gallery, diff |
| AuditViewer | Software platform and integrations | stable | catalog-variant-gallery |
| PlainTextEditor | Editors and documents | stable | catalog-variant-gallery |
| StreamingLogViewer | Editors and documents | stable | catalog-variant-gallery |
| TerminalOutput | Editors and documents | stable | catalog-variant-gallery |
| FileBrowser | Editors and documents | stable | catalog-variant-gallery |
| DirectoryTree | Editors and documents | stable | catalog-variant-gallery |
| AttachmentGallery | Editors and documents | stable | catalog-variant-gallery |
| ImageViewer | Editors and documents | stable | catalog-variant-gallery |
| ImageAnnotator | Editors and documents | stable | catalog-variant-gallery |
| DocumentMetadata | Editors and documents | stable | catalog-variant-gallery |
| PropertyInspector | Editors and documents | stable | catalog-variant-gallery |
| SchemaViewer | Editors and documents | stable | catalog-variant-gallery |
| APIResponseInspector | Editors and documents | stable | catalog-variant-gallery |
| ObjectInspector | Editors and documents | stable | catalog-variant-gallery |
| Comments | Collaboration and workflow | stable | catalog-variant-gallery |
| ThreadedComments | Collaboration and workflow | stable | catalog-variant-gallery |
| Mentions | Collaboration and workflow | stable | catalog-variant-gallery |
| ActivityFeed | Collaboration and workflow | stable | catalog-variant-gallery |
| AuditTimeline | Collaboration and workflow | stable | catalog-variant-gallery |
| ApprovalPanel | Collaboration and workflow | stable | catalog-variant-gallery |
| ApprovalFlow | Collaboration and workflow | stable | catalog-variant-gallery |
| Assignment | Collaboration and workflow | stable | catalog-variant-gallery |
| OwnerPicker | Collaboration and workflow | stable | catalog-variant-gallery |
| TeamPicker | Collaboration and workflow | stable | catalog-variant-gallery |
| Watchers | Collaboration and workflow | stable | catalog-variant-gallery |
| Followers | Collaboration and workflow | stable | catalog-variant-gallery |
| Labels | Collaboration and workflow | stable | catalog-variant-gallery |
| Checklist | Collaboration and workflow | stable | catalog-variant-gallery |
| TaskList | Collaboration and workflow | stable | catalog-variant-gallery |
| StatusTransition | Collaboration and workflow | stable | catalog-variant-gallery |
| WorkflowStepper | Collaboration and workflow | stable | catalog-variant-gallery |
| Escalation | Collaboration and workflow | stable | catalog-variant-gallery |
| NotificationPreferences | Collaboration and workflow | stable | catalog-variant-gallery |
| Presence | Collaboration and workflow | stable | catalog-variant-gallery |
| ConflictResolution | Collaboration and workflow | stable | catalog-variant-gallery |
| RevisionHistory | Collaboration and workflow | stable | catalog-variant-gallery |
| UserDirectory | Administration | stable | catalog-variant-gallery |
| MemberTable | Administration | stable | catalog-variant-gallery |
| RoleManager | Administration | stable | catalog-variant-gallery |
| PermissionMatrix | Administration | stable | catalog-variant-gallery, permissions |
| TenantSelector | Administration | stable | catalog-variant-gallery |
| TenantAdministration | Administration | stable | catalog-variant-gallery |
| FeatureFlagManager | Administration | stable | catalog-variant-gallery |
| Settings | Administration | stable | catalog-variant-gallery |
| Preferences | Administration | stable | catalog-variant-gallery |
| ThemeSettings | Administration | stable | catalog-variant-gallery |
| AuditConsole | Administration | stable | catalog-variant-gallery |
| HealthDashboard | Administration | stable | catalog-variant-gallery |
| RuntimeDiagnostics | Administration | stable | catalog-variant-gallery |
| StorageDiagnostics | Administration | stable | catalog-variant-gallery |
| APIConnectivity | Administration | stable | catalog-variant-gallery |
| EnvironmentInfo | Administration | stable | catalog-variant-gallery |
| AppShell | Layouts | stable | catalog-variant-gallery |
| SidebarShell | Layouts | stable | catalog-variant-gallery |
| TopNavShell | Layouts | stable | catalog-variant-gallery |
| DualSidebarShell | Layouts | stable | catalog-variant-gallery |
| HeaderContent | Layouts | stable | catalog-variant-gallery |
| HeaderToolbarContent | Layouts | stable | catalog-variant-gallery |
| SingleColumn | Layouts | stable | catalog-variant-gallery |
| TwoColumn | Layouts | stable | catalog-variant-gallery |
| ThreeColumn | Layouts | stable | catalog-variant-gallery |
| DashboardGrid | Layouts | stable | catalog-variant-gallery |
| MasterDetail | Layouts | stable | catalog-variant-gallery |
| SplitHorizontal | Layouts | stable | catalog-variant-gallery |
| SplitVertical | Layouts | stable | catalog-variant-gallery |
| ResizableSplit | Layouts | stable | catalog-variant-gallery |
| InspectorLayout | Layouts | stable | catalog-variant-gallery |
| StickyHeader | Layouts | stable | catalog-variant-gallery |
| StickyFooter | Layouts | stable | catalog-variant-gallery |
| StickySidebar | Layouts | stable | catalog-variant-gallery |
| FullHeightWorkspace | Layouts | stable | catalog-variant-gallery |
| CanvasWorkspace | Layouts | stable | catalog-variant-gallery |
| DenseOperationsWorkspace | Layouts | stable | catalog-variant-gallery |
| CenteredForm | Layouts | stable | catalog-variant-gallery |
| DossierLayout | Layouts | stable | catalog-variant-gallery |
| ResponsiveCards | Layouts | stable | catalog-variant-gallery |
| AccessKeyIdentity | Platform services | stable | catalog-variant-gallery |
| TenantIsolation | Platform services | stable | catalog-variant-gallery |
| Authorization | Platform services | stable | catalog-variant-gallery |
| ServerPagination | Platform services | stable | catalog-variant-gallery |
| GeneratedAPIContracts | Platform services | stable | catalog-variant-gallery |
| Transactions | Platform services | stable | catalog-variant-gallery |
| MigrationHistory | Platform services | stable | catalog-variant-gallery |
| ConfigDatabaseMigrations | Platform services | stable | catalog-variant-gallery |
| AttachmentsProtection | Platform services | stable | catalog-variant-gallery |
| Idempotency | Platform services | stable | catalog-variant-gallery |
| OptimisticConcurrency | Platform services | stable | catalog-variant-gallery |
| AuditPersistence | Platform services | stable | catalog-variant-gallery |
| BackupManifest | Platform services | stable | catalog-variant-gallery |
| IsolatedRestore | Platform services | stable | catalog-variant-gallery |
| MigrationRehearsal | Platform services | stable | catalog-variant-gallery |
| DirectDatabaseSDK | Platform services | stable | catalog-variant-gallery |
| ImportPreview | Platform services | stable | catalog-variant-gallery |
| CSVExchange | Platform services | stable | catalog-variant-gallery |
| XLSXExchange | Platform services | stable | catalog-variant-gallery |
| RevisionRevert | Platform services | stable | catalog-variant-gallery |
| SavedViewsPersistence | Platform services | stable | catalog-variant-gallery |
| DurableJobs | Platform services | stable | catalog-variant-gallery |
| WebhooksOutbound | Platform services | stable | catalog-variant-gallery |
| WebhooksInbound | Platform services | stable | catalog-variant-gallery |
| RealtimeBus | Platform services | stable | catalog-variant-gallery |
| IntegrationCredentials | Platform services | stable | catalog-variant-gallery |
| RateLimits | Platform services | stable | catalog-variant-gallery |
| HealthReadiness | Platform services | stable | catalog-variant-gallery |
| StructuredLogging | Platform services | stable | catalog-variant-gallery |
| OTelMetrics | Platform services | stable | catalog-variant-gallery |
| OTelTraces | Platform services | stable | catalog-variant-gallery |
| NotificationDelivery | Platform services | stable | catalog-variant-gallery |
| ApplicationGenerator | Platform services | stable | catalog-variant-gallery |
| WorkspaceGenerator | Platform services | stable | catalog-variant-gallery |
| UpgradePlanner | Platform services | stable | catalog-variant-gallery |
| UpgradeApply | Platform services | stable | catalog-variant-gallery |
| UpgradeRollback | Platform services | stable | catalog-variant-gallery |
| ExperienceLab | Developer and certification | stable | catalog-variant-gallery |
| Storybook | Developer and certification | stable | catalog-variant-gallery |
| ThemeStudio | Developer and certification | stable | catalog-variant-gallery |
| ArchitectureRules | Developer and certification | stable | catalog-variant-gallery |
| DependencyLocks | Developer and certification | stable | catalog-variant-gallery |
| SecretScanning | Developer and certification | stable | catalog-variant-gallery |
| AdvisoryScanning | Developer and certification | stable | catalog-variant-gallery |
| SAST | Developer and certification | stable | catalog-variant-gallery |
| SBOM | Developer and certification | stable | catalog-variant-gallery |
| Provenance | Developer and certification | stable | catalog-variant-gallery |
| CleanMacSetup | Developer and certification | stable | catalog-variant-gallery |
| CorporatePaaSPublish | Developer and certification | stable | catalog-variant-gallery |
| CorporateStorageQualification | Developer and certification | stable | catalog-variant-gallery |
| CorporateIdentityQualification | Developer and certification | stable | catalog-variant-gallery |
| VisualRegression | Developer and certification | stable | catalog-variant-gallery |
| KeyboardRegression | Developer and certification | stable | catalog-variant-gallery |
| AccessibilityAssessment | Developer and certification | stable | catalog-variant-gallery |
| PerformanceBudgets | Developer and certification | stable | catalog-variant-gallery |
| SourceCheckpoints | Developer and certification | stable | catalog-variant-gallery |
| CatalogCompleteness | Developer and certification | stable | catalog-variant-gallery |
| APIContractDrift | Developer and certification | stable | catalog-variant-gallery |
| DocumentationChecks | Developer and certification | stable | catalog-variant-gallery |
