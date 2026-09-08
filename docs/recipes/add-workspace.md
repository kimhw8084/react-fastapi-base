# Add a concrete workspace

Create backend/app/features/<name> with concrete models, schemas, services, definition and router, following work_items. Add its trusted module name to features/manifest.json and a navigation item to config/application.json. The feature registry is trusted deployment code, not user input. Assign unique operation IDs and a stable workspace key. Add tenant migration and new tests; keep permissions server-enforced.

Create frontend/src/features/<name>/adapter.tsx and Workspace.tsx. Register the renderer in frontend/src/app/registry.tsx. A TableWorkspace consumer supplies list/get/create/update/bulk/history/revert/export hooks and supported slots. A non-table feature can render a bespoke React body through the same registry; do not fake unsupported actions just to fit the adapter.

Run ./dev contracts and both code/browser gates. There is no automatic workspace generator in this build. Shared-view schemas must explicitly declare allowed columns/filters/sorts; arbitrary unvalidated JSON must not become query code. Do not copy a whole giant SysGrid component and relabel it as a template feature.
