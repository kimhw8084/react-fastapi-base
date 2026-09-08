> **1.0.0-rc.1 update:** this historical 68-domain ledger remains a traceable baseline. Current implementation status is maintained in [v1-completion-status.json](v1-completion-status.json), generated contracts, migrations, tests, and current evidence. No status is promoted by a screenshot or file count.

# React-FastAPI Base — 68-domain scope ledger

Version 1.0.0-rc.1. **Not production certified.** No percentage-complete score is asserted. “Implemented” means the bounded contract has source and executed evidence; it does not certify the full upstream, browser, OS, or company scope.

| ID | Domain | Status | Owner |
|---|---|---|---|
| G01 | Mission and quality bar | PARTIAL | README.md; docs/MASTER_DESIGN.md |
| G02 | Company PaaS contract | EXTERNAL | deploy/; docs/DEPLOYMENT.md |
| G03 | Core architecture boundaries | IMPLEMENTED | backend/app/platform/; frontend/src/platform/; scripts/check_architecture.py |
| G04 | Template and package architecture | PARTIAL | scripts/template_tools.py |
| G05 | Upgrade strategy | PARTIAL | scripts/template_tools.py; docs/UPGRADING.md |
| G06 | Customization model | PARTIAL | backend/app/config/; frontend/src/app/registry.tsx; frontend/src/platform/workspace/types.ts |
| G07 | Runtime configuration | IMPLEMENTED | frontend/public/runtime-config.json; frontend/src/platform/api/runtime.ts; backend/app/platform/configuration.py |
| G08 | Branding and design system | PARTIAL | frontend/src/theme/ |
| G09 | SysGrid visual DNA | PARTIAL | docs/SYSGRID_EXTRACTION.md |
| G10 | Application shell | PARTIAL | frontend/src/app/Application.tsx |
| G11 | Workspace engine and DSL | PARTIAL | backend/app/platform/workspace_registry.py; frontend/src/app/registry.tsx |
| G12 | Contract ownership | IMPLEMENTED | scripts/generate_contracts.py; contracts/openapi.json; frontend/src/generated/schema.ts |
| G13 | Operational grid | PARTIAL | frontend/src/platform/grid/DataGrid.tsx; frontend/src/platform/workspace/TableWorkspace.tsx |
| G14 | Saved workspace state | PARTIAL | backend/app/platform/views.py; frontend/src/platform/workspace/SavedViews.tsx |
| G15 | Forms | PARTIAL | frontend/src/platform/workspace/RecordForm.tsx |
| G16 | Modals and overlays | PARTIAL | frontend/src/platform/ui/Dialog.tsx |
| G17 | Details, history and compare | PARTIAL | frontend/src/platform/workspace/Dossier.tsx; backend/app/features/work_items/service.py |
| G18 | Lifecycle | PARTIAL | backend/app/features/work_items/ |
| G19 | AccessKey identity | EXTERNAL | backend/app/profiles/company/identity.py; backend/app/platform/settings.py |
| G20 | Authorization and users | PARTIAL | backend/app/platform/policy.py; backend/app/platform/security.py; backend/app/config/permissions.json |
| G21 | Tenancy | PARTIAL | backend/app/platform/database.py; backend/app/platform/models.py |
| G22 | Backend architecture | IMPLEMENTED | backend/app/main.py; backend/app/platform/; backend/app/features/ |
| G23 | API contract | PARTIAL | contracts/openapi.json; frontend/src/platform/api/client.ts |
| G24 | Frontend data architecture | PARTIAL | frontend/src/platform/api/; frontend/src/platform/workspace/ |
| G25 | Database architecture | IMPLEMENTED | backend/migrations/; backend/app/platform/database.py |
| G26 | Mounted SQLite qualification | EXTERNAL | backend/app/profiles/company/storage_probe.py; deploy/company-qualification.template.json |
| G27 | Direct DB tooling | PARTIAL | backend/app/tooling/work_items.py |
| G28 | File storage | PARTIAL | backend/app/platform/attachments.py |
| G29 | Migrations, backup and recovery | PARTIAL | backend/app/platform/backup.py; docs/RECOVERY.md |
| G30 | Import and export | PARTIAL | backend/app/features/work_items/exchange.py |
| G31 | External integrations | DESIGNED | docs/MASTER_DESIGN.md |
| G32 | Background and scheduled work | DESIGNED | docs/MASTER_DESIGN.md |
| G33 | Realtime | DESIGNED | docs/MASTER_DESIGN.md |
| G34 | Audit | PARTIAL | backend/app/platform/audit.py; backend/migrations/tenant/0001_tenant.py |
| G35 | Errors and diagnostics | IMPLEMENTED | backend/app/platform/errors.py; frontend/src/platform/api/client.ts |
| G36 | Observability | PARTIAL | backend/app/platform/middleware.py; backend/app/main.py |
| G37 | Security model | PARTIAL | docs/SECURITY.md; backend/tests/test_security.py |
| G38 | Supply chain | BLOCKED | backend/requirements.lock; frontend/package.json; .github/workflows/verify.yml |
| G39 | Accessibility | BLOCKED | frontend/tests/e2e/; frontend/src/platform/ui/ |
| G40 | Performance | DESIGNED | docs/MASTER_DESIGN.md |
| G41 | Browser and devices | BLOCKED | frontend/playwright.config.ts; frontend/src/theme/ |
| G42 | Locale and time | PARTIAL | backend/app/platform/schemas.py; frontend/src/generated/schema.ts |
| G43 | Notifications | PARTIAL | frontend/src/platform/ui/Notice.tsx |
| G44 | Flags and capabilities | PARTIAL | backend/app/features/work_items/definition.py; backend/app/platform/policy.py |
| G45 | Developer commands | IMPLEMENTED | dev; scripts/ |
| G46 | Development environments | PARTIAL | dev; scripts/e2e_runner.py; deploy/ |
| G47 | Test architecture | PARTIAL | evidence/verification/; backend/tests/; frontend/tests/ |
| G48 | Golden behavioral contracts | PARTIAL | backend/tests/; scripts/check_architecture.py |
| G49 | Authoritative verification | PARTIAL | scripts/verify.py |
| G50 | CI/CD | PARTIAL | .github/workflows/verify.yml |
| G51 | Native PaaS adapters | EXTERNAL | deploy/; frontend/server.mjs; backend/run.py |
| G52 | Codex workflow | IMPLEMENTED | AGENTS.md; docs/CODEX.md |
| G53 | Agent-friendly organization | PARTIAL | frontend/src/; backend/app/; docs/recipes/ |
| G54 | Architecture linting | PARTIAL | scripts/check_architecture.py |
| G55 | Generators | PARTIAL | scripts/template_tools.py |
| G56 | Documentation | IMPLEMENTED | docs/; README.md |
| G57 | Neutral reference feature | PARTIAL | backend/app/features/work_items/; frontend/src/features/work-items/ |
| G58 | Reference variants | PARTIAL | tests/test_template_tools.py; frontend/src/theme/tokens.css |
| G59 | Exhaustive SysGrid file audit | INCOMPLETE | docs/SYSGRID_EXTRACTION.md; SOURCE_PROVENANCE.json |
| G60 | SysGrid behavior inventory | INCOMPLETE | docs/SYSGRID_EXTRACTION.md |
| G61 | SysGrid migration | INCOMPLETE | docs/SYSGRID_MIGRATION.md |
| G62 | Technical-debt cleanup | PARTIAL | docs/ADRS.md |
| G63 | Repository hygiene | PARTIAL | .gitignore; scripts/template_tools.py |
| G64 | Platform governance | DESIGNED | docs/MASTER_DESIGN.md; docs/UPGRADING.md |
| G65 | Release certification | BLOCKED | docs/RELEASE_STATUS.md; evidence/verification/verification.json |
| G66 | Home/cloud extension points | DESIGNED | docs/MASTER_DESIGN.md |
| G67 | Success metrics | DESIGNED | docs/MASTER_DESIGN.md |
| G68 | Decision records | IMPLEMENTED | docs/ADRS.md |
