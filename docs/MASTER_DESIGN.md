> **Implementation addendum (1.0.0-rc.7):** see decisions/0001-native-widget-layer.md, EXPERIENCE_LAB.md, COMPONENT_COVERAGE.md and v1-completion-status.json. The qualification environment and prerequisite contract are explicit; this candidate also carries the bounded shared UI remediation and rendered evidence. Final company qualification remains external. This design is not itself production evidence.

# React-FastAPI Base Platform — master design and implementation contract

**Version: 1.0.0-rc.7 · Reference: SysGrid 66244b997a70b85e6e887870c96db958f3f0d22d · Release: NOT_CERTIFIED**

This document is a design baseline with an executable initial implementation, not a claim that the previously requested entire platform is finished. The 68-domain ledger is authoritative about missing scope. Changes to SysGrid itself, complete visual parity, advanced workspace archetypes, actual corporate publication, dependency-resolved React verification and a production release are not included as completed work.

## 1. Mission and decisions

Build repeatable company operational applications from a shared React/Vite/AG Grid frontend and FastAPI/SQLAlchemy/Alembic/SQLite backend. Preserve the company's independent native application publishers. Keep the company's identity source behind one adapter. Keep feature-specific business rules explicit. Maximize customization through typed configuration and feature composition without teaching agents to edit the kernel for every screen.

A template is not an authorization to ignore storage or identity constraints. The company profile is provisionally supported only when the actual platform makes its identity and persistence contracts true. `AccessKey` is process environment, not a per-request identity protocol. A shared process cannot safely represent different users merely by rereading that variable. The operator must demonstrate distinct user execution/routing. The storage probe is diagnostic only. A path which looks local may lack SQLite's required locking and durability. AWS Mountpoint is an example of an S3 file interface that does not provide a database-compatible ordinary filesystem; this does not identify which provider the company actually uses. [S1–S4]

## 2. Dependency direction and source ownership

```text
backend app composition + trusted feature registry
  ├─ concrete features / services / domain models
  ├─ company identity adapter
  └─ generic platform: transport, authorization, transaction, audit, saved views, recovery

frontend app composition + renderer registry
  ├─ feature adapter / custom components
  ├─ typed generated API contracts
  ├─ app theme and nonsecret runtime config
  └─ generic platform: shell primitives, workspace, forms, dialogs, API, preferences
```

A platform module must not import a product feature. The app composition root may import both. The backend registry lists trusted local module names; there is no user-uploaded code/plugin loader. The generic workspace has presentation metadata, not a generic entity database. Work-item invariants live in work-items services and schemas. A future reservations feature must enforce overlap rules in its own service/transaction, not in UI metadata.

## 3. Configuration and customization contract

| Concern | Authority | Change mechanism |
|---|---|---|
| Product ID, name, description, navigation labels/order | backend/app/config/application.json | Validated file; backend restart |
| Role permission sets | backend/app/config/permissions.json | Trusted server-only config; restart and negative tests |
| Actual memberships | registry database | Explicit operator tooling; no default admin grant on login |
| API origin, default theme, optional title override | frontend/public/runtime-config.json | Static publisher update; Node publisher can reread an external runtime file |
| Visual tokens and complete themes | frontend/src/theme | Source edit and frontend rebuild |
| Field definitions and business validation | feature Pydantic schemas and definition | Edit feature, migrate if necessary, regenerate contracts |
| Feature component/renderer | frontend/src/app/registry.tsx + feature directory | React code, no kernel patch |
| Tenant/user working state | platform storage key service | App/user/tenant/version namespace; no secret data |
| Shared saved views | tenant database | Server authorization and revisioned API |
| Production data root, limits, origins, qualification | BASE_ environment + operator evidence | Server-only; never in browser runtime JSON |

Precedence is explicit: runtime title override wins over backend application name. A saved user theme wins over frontend runtime default; frontend runtime default is the browser bootstrap theme source. The application generator updates both theme files consistently. Backend density feeds the workspace default; saved user/workspace density can override it. Navigation order comes from backend configuration; labels are consumed by the shell. Theme/labels may change without granting permissions. Runtime hiding of a control never changes server authority.

The current implementation supports one neutral entity and three themes. Maximum theoretical customization is not proven by those fixtures. At least a second concrete domain, a different shell structure and a bespoke analytical body must be exercised before Golden v1. Avoid adding flags for every JSX detail: expose composition slots and let features remain ordinary React.

## 4. Data, authorization and concurrency

Registry database: tenant UUID, tenant name/active state and membership keyed by tenant plus company username. Tenant database: concrete domain records, saved views, audit events, idempotency results and small attachment BLOBs. Tenant IDs are canonical UUIDs; paths are derived by the database adapter and constrained to the configured root. No raw client path selects a database. Missing files fail; request-time opening does not recreate a missing database. Startup does not migrate schemas.

The company adapter rejects missing/malformed AccessKey rather than substituting admin. Development identity is an explicit local/test fixture. A request selects a tenant through X-Tenant-Id; server membership is checked every time. A frontend API client is immutable with respect to tenant so in-flight requests cannot inherit a different tenant after a switch. Query keys include user and tenant.

Writes require a CSRF token bound to the resolved username and accepted explicit Origin when present. The token is not an authentication credential or replacement for authenticated ingress. Corporate cookies/routing remain the PaaS responsibility. Mutation permissions are enforced in domain services. Viewers can maintain personal views but cannot alter domain records. “Team” views currently mean tenant-wide; true corporate group membership is not implemented.

SQLite writes use a short BEGIN IMMEDIATE transaction, then authorization-sensitive read, revision validation, conditional update, audit append and commit. A stale revision returns 409. Bulk actions apply only explicit ID/revision pairs and roll back the entire batch on any stale or invalid item. Create/import/bulk replay endpoints accept idempotency keys scoped to the user and operation. Reusing a key with a different payload is a conflict. Generic auto-retry of writes is prohibited; a UI retry of an uncertain request must preserve its original operation key.

The implementation uses synchronous SQLAlchemy with synchronous FastAPI route functions. This is a deliberate bounded choice for short SQLite transactions and direct trusted Python tools; it is not a claim that async SQLAlchemy is bad. FastAPI runs synchronous route functions in its threadpool. [S5] External async I/O or another database may justify a separate adapter. The backend supports Python `>=3.11,<3.15`; current release evidence records Python 3.14.5, and the company's actual runtime must be exercised during qualification.

## 5. Files, import/export and recovery

Small attachment payloads are stored as BLOBs with metadata in the same tenant database. This simplifies atomicity and backup scope at the cost of database growth. Current limits are one megabyte and a short MIME/magic allowlist. Forced binary downloads avoid inline active-content rendering. This is not malware scanning. Large documents/object storage, scanning/CDR and retention need a real provider pack before expanding the upload envelope.

CSV, dependency-free XLSX, and versioned JSON snapshots are explicit exchange formats, not raw database dumps. Cells that could become spreadsheet formulas are escaped reversibly, and import restores escaping only for this versioned contract. Preview validates every row. Commit requires the preview fingerprint and revalidates the payload; all rows are inserted atomically. It does not overwrite matching records or restore IDs/history. Imports are capped at 100 rows, exports at 1,000 filtered records. Multi-entity relationship snapshots and background imports remain unfinished.

Each database is snapshotted with SQLite's backup API. Whole-application consistency across registry and tenant files additionally requires stopping all writers during the multi-file snapshot. The APP-STOPPED argument records operator acknowledgement only; it cannot discover every external client. Manifests bind roles/relative paths/sizes/hashes. Restore refuses unsafe paths, checksum failures, invalid SQLite state or a nonempty destination. Restore to a new root, rehearse migrations, then promote under maintenance. Application rollback and data restoration are separate changes. Never copy a live SQLite main file and assume it is a consistent backup.

## 6. API and UI contracts

Pydantic/FastAPI owns the wire schema. Generated OpenAPI and TypeScript types plus operation metadata are committed, and drift fails verification. This review build includes a limited deterministic schema emitter, not a general replacement for mature OpenAPI tooling. New schema forms require emitter tests or migration to a qualified standard generator. [S6]

Errors have code/message/details/request_id. The browser renders errors as failures, never as empty successful lists. The reference list uses server filtering/global sort/pagination. AG Grid local column sorting is explicitly described as loaded-page-only. This distinction must survive future grouping/export changes. Grouping and full SysGrid context-menu/shift-range semantics are not implemented in this review build.

Forms use the authoritative field metadata and Pydantic validation. Custom React slots remain available for complex domain fields. The native dialog owns Escape/close/dirty confirmation, instead of every feature inventing listeners and z-index rules. Native dialog semantics are a useful baseline, not accessibility certification. [S7] Browser Back/Forward, zoom, nested overlays and screen-reader behavior require actual tests. Reversion creates a new revision with a new audit event; it never rewrites history.

## 7. Packaging, upgrades and workflow

The current output is a source template rather than published npm/Python packages. `./dev create` writes a new destination only, changes app config/runtime values, excludes private/generated execution state and records managed-core hashes. `./dev upgrade-plan` compares the app's original core hashes, its current files and an incoming template. Conflicts are surfaced; `./dev upgrade-apply` performs hash-bound atomic managed-core updates and `./dev upgrade-rollback` restores a journaled snapshot while refusing post-upgrade human edits. `./dev upgrade-fixture` exercises the generated-app migration/build/test/rollback path.

The template's AGENTS.md applies only to this new repository. It does not supersede SysGrid's control-room workflow. No commit, push, production migration or publication is performed by the supplied verification/generation commands. Developers work in config, theme and feature directories first. Kernel changes need evidence of a cross-feature concern and associated regression tests.

## 8. Proposed operational budgets and compatibility envelope

These are targets to verify, not measured results: p95 ordinary CRUD API latency under 500 ms at 20 active users on representative company hardware; common interaction latency under 200 ms; initial compressed JavaScript under 600 KiB unless an explicit AG Grid/tooling exception is justified; no unbounded user result sets; no full-table browser dataset needed for ordinary pages. Measure p95/p99 lock waits and maximum memory, not only a single successful request. Exports/imports must fail before expensive work when limits are exceeded. Load beyond the tested envelope requires a new supported profile, not merely a larger timeout.

Current locally verified envelope: Python 3.11–3.14 as declared by the backend, Node 22 in the locked frontend environment, React 18.3.1, Vite 8.2.2, React Router 7.18.3, TanStack Query 5.102.8, and AG Grid Community 36.1.0. `npm ci`, the React production build, Storybook, and Playwright browser gates are current evidence for this checkout. The company Node/Python runtime still requires its own qualification.

## 9. Optional packs: exact boundaries, not phantom implementations

External integrations implement an application-owned adapter with a typed request/result, explicit allowed origins, secret reference, timeout and idempotency strategy. They cannot accept arbitrary untrusted URLs without SSRF protection. Webhooks need signature verification and replay storage. No provider implementation is included.

Background work needs a durable job record with id, tenant, requested-by, payload version, status, attempts, idempotency key, lease owner/expiry and fencing/version token. Side effects must be idempotent. This design is not implemented, and safe leases depend on the qualified database topology. A shared SQLite file on an unqualified multi-host mount is not a job coordinator.

Realtime subscriptions must authorize the actor and tenant at subscription time, reauthorize when access changes and publish minimal versioned invalidation events. No global broadcast to all users. No transport is implemented in this build.

Cloud/home profile changes identity to a verified session/OIDC adapter, storage to a service/object adapter, and database to a separately tested PostgreSQL implementation. Current SQLite triggers, migrations and backup tooling are not portable simply by changing a connection URL. Billing, AI/RAG, public signup and marketplaces are later application packs, not company-kernel dependencies.

## 10. Release truth and completion sequencing

A successful local test suite is not company certification. `scripts/verify.py` separates executable code gates from deployment/migration evidence. Missing dependencies/tools are BLOCKED rather than SKIPPED. A returned `code_ready` can only describe executed code gates; production_ready is not granted by this script. Release approval must identify an exact source/artifact digest and attach upstream dependency scans, actual browser proof, provider/identity evidence, recovery drill and remaining scope closure.

Immediate order: resolve/review dependencies; run actual strict TS/component/build/browser/a11y checks and repair failures; complete advanced baseline UX and navigation safety; prove a second domain/custom body; complete SysGrid audit and one migration; implement safe upgrade apply; run supply-chain and company qualification; only then consider a v1 release. Do not increase retries, weaken tests or replace real application proof with mock snapshots to obtain a green result.

## 11. Complete retained 68-domain contract

Every domain below remains in scope. “Designed” and “partial” are intentionally not called implemented. Each record names the next acceptance obligation so another implementer can continue without silently discarding requirements.

### G01 — Mission and quality bar

**State:** PARTIAL. **Owner:** `README.md; docs/MASTER_DESIGN.md`.

**Decision:** A company-first, configurable operational-app foundation; no automatic production certification.

**Acceptance obligation:** Deliver the complete declared feature and verification scope before v1; no critical open release issues.

### G02 — Company PaaS contract

**State:** EXTERNAL. **Owner:** `deploy/; docs/DEPLOYMENT.md`.

**Decision:** Independent backend/ and frontend/ roots; native FastAPI and static React/optional Node entrypoints; no Docker prerequisite.

**Acceptance obligation:** Publish both projects on the real PaaS, test authenticated cross-origin routing, restarts and persistent state.

### G03 — Core architecture boundaries

**State:** IMPLEMENTED. **Owner:** `backend/app/platform/; frontend/src/platform/; scripts/check_architecture.py`.

**Decision:** Application composition injects feature definitions and renderers into a feature-independent kernel.

**Acceptance obligation:** Architecture checks reject known inverse imports, raw transport, unscoped browser storage and identity adapter bypasses.

### G04 — Template and package architecture

**State:** PARTIAL. **Owner:** `scripts/template_tools.py`.

**Decision:** Vendored source template with an explicit managed-core manifest; app-specific code remains outside core ownership.

**Acceptance obligation:** Test clean generation, independent native publishers, no accidental credential/evidence inheritance; package publication remains optional.

### G05 — Upgrade strategy

**State:** PARTIAL. **Owner:** `scripts/template_tools.py; docs/UPGRADING.md`.

**Decision:** Three-way hash-based dry-run plan; never overwrite local divergence; no automatic merge or apply yet.

**Acceptance obligation:** Implement reviewed atomic apply, rollback, compatibility migration and a real v0-to-v1 upgrade fixture.

### G06 — Customization model

**State:** PARTIAL. **Owner:** `backend/app/config/; frontend/src/app/registry.tsx; frontend/src/platform/workspace/types.ts`.

**Decision:** Typed configuration, injected adapters and custom React renderers; no universal generic database entity.

**Acceptance obligation:** Prove materially different complete applications, not just three theme JSON variants, without changing platform code.

### G07 — Runtime configuration

**State:** IMPLEMENTED. **Owner:** `frontend/public/runtime-config.json; frontend/src/platform/api/runtime.ts; backend/app/platform/configuration.py`.

**Decision:** Strict nonsecret JSON for API origin, title and theme; server-owned configuration and permissions are separate.

**Acceptance obligation:** Unknown keys, unsafe origins and HTTPS-to-HTTP routing must fail; secrets never enter browser configuration.

### G08 — Branding and design system

**State:** PARTIAL. **Owner:** `frontend/src/theme/`.

**Decision:** Semantic CSS tokens with operations, clarity and minimal themes; no Tailwind dependency in this review build.

**Acceptance obligation:** Run real visual/a11y tests, add logo/icon/i18n configuration, remove remaining fixed presentation decisions through named tokens.

### G09 — SysGrid visual DNA

**State:** PARTIAL. **Owner:** `docs/SYSGRID_EXTRACTION.md`.

**Decision:** Monitoring behavioral patterns inform shared table, modal, saved-view and dossier ownership; no pixel-parity claim.

**Acceptance obligation:** Capture approved live SysGrid references by viewport/theme and compare the actual built template.

### G10 — Application shell

**State:** PARTIAL. **Owner:** `frontend/src/app/Application.tsx`.

**Decision:** Registered workspaces, navigation labels, tenant selection, themes, identity display, bootstrap and error states.

**Acceptance obligation:** Add configurable shell variants, global search, notification surface and permission-aware multi-feature navigation proof.

### G11 — Workspace engine and DSL

**State:** PARTIAL. **Owner:** `backend/app/platform/workspace_registry.py; frontend/src/app/registry.tsx`.

**Decision:** Pydantic definitions provide fields, columns, filters, sort keys and capabilities; app-owned renderer registry allows custom bodies.

**Acceptance obligation:** Implement and verify additional table, hybrid, analytical and topology archetypes without coercing domain behavior into CRUD.

### G12 — Contract ownership

**State:** IMPLEMENTED. **Owner:** `scripts/generate_contracts.py; contracts/openapi.json; frontend/src/generated/schema.ts`.

**Decision:** Pydantic/FastAPI owns API and workspace contracts; generate OpenAPI, TypeScript data shapes and operation metadata.

**Acceptance obligation:** Generation is deterministic and --check fails on drift; qualify generator support before introducing new schema constructs.

### G13 — Operational grid

**State:** PARTIAL. **Owner:** `frontend/src/platform/grid/DataGrid.tsx; frontend/src/platform/workspace/TableWorkspace.tsx`.

**Decision:** AG Grid Community adapter with selection, column persistence, server pagination, global sort/filter controls and local page sorting.

**Acceptance obligation:** Finish grouped/range selection, context menus, visibility UI, utility columns and SysGrid interaction parity; full browser proof required.

### G14 — Saved workspace state

**State:** PARTIAL. **Owner:** `backend/app/platform/views.py; frontend/src/platform/workspace/SavedViews.tsx`.

**Decision:** Personal and tenant-shared views, exact deep links, schema sanitization, optimistic revisions and conflict errors.

**Acceptance obligation:** Add true directory-team scopes, favorites/defaults, explicit conflict-resolution UI and offline reconciliation; tenant-wide shared is not corporate team membership.

### G15 — Forms

**State:** PARTIAL. **Owner:** `frontend/src/platform/workspace/RecordForm.tsx`.

**Decision:** Definition-driven basic fields, validation, custom field slots, native dialog dirty protection and pending-write disabling.

**Acceptance obligation:** Verify browser Back/Forward and all navigation paths preserve dirty drafts; add dependent selectors, tabs, async validation and field-level custom constraints.

### G16 — Modals and overlays

**State:** PARTIAL. **Owner:** `frontend/src/platform/ui/Dialog.tsx`.

**Decision:** Native dialog with nested discard confirmation, focus return and busy lock.

**Acceptance obligation:** Qualify focus/keyboard behavior in real browsers and add anchored dropdown/context-menu overlay ownership and collision geometry.

### G17 — Details, history and compare

**State:** PARTIAL. **Owner:** `frontend/src/platform/workspace/Dossier.tsx; backend/app/features/work_items/service.py`.

**Decision:** Deep-linked dossiers, structured audit deltas and revision-target reversion for the reference feature.

**Acceptance obligation:** Add arbitrary two-version comparison, linked-record panels and complex entity dossier slots; run permissions and stale-revert tests.

### G18 — Lifecycle

**State:** PARTIAL. **Owner:** `backend/app/features/work_items/`.

**Decision:** Work-item create/update/archive/restore/revert with explicit revision checks and atomic bulk operations.

**Acceptance obligation:** Do not advertise purge/delete where no endpoint exists; add declared domain-specific lifecycle policies and irreversible-action acceptance.

### G19 — AccessKey identity

**State:** EXTERNAL. **Owner:** `backend/app/profiles/company/identity.py; backend/app/platform/settings.py`.

**Decision:** Company adapter reads AccessKey only; no browser-supplied username fallback; production requires per-user process evidence.

**Acceptance obligation:** Two real simultaneous users must get their own username; if one shared process exposes one username, stop rollout and resolve topology.

### G20 — Authorization and users

**State:** PARTIAL. **Owner:** `backend/app/platform/policy.py; backend/app/platform/security.py; backend/app/config/permissions.json`.

**Decision:** Server-owned roles with editable permission sets and CLI membership provisioning; browser flags are never authority.

**Acceptance obligation:** Complete membership revoke/role-change administration and review object-level policies for new domains; negative tests are mandatory.

### G21 — Tenancy

**State:** PARTIAL. **Owner:** `backend/app/platform/database.py; backend/app/platform/models.py`.

**Decision:** Registry plus UUID-addressed tenant databases, server-checked membership, tenant-scoped API clients and cache keys.

**Acceptance obligation:** Add tenant disable/recovery management and a separately tested single-database profile; multi-host direct SQLite remains unsupported.

### G22 — Backend architecture

**State:** IMPLEMENTED. **Owner:** `backend/app/main.py; backend/app/platform/; backend/app/features/`.

**Decision:** Synchronous SQLAlchemy and synchronous FastAPI routes for short SQLite operations; domain services and transactions remain explicit.

**Acceptance obligation:** Keep blocking I/O out of async handlers; introduce async only for a demonstrated adapter need with independent tests.

### G23 — API contract

**State:** PARTIAL. **Owner:** `contracts/openapi.json; frontend/src/platform/api/client.ts`.

**Decision:** Explicit operation IDs, generated typed calls, validation/error envelopes, request IDs, revisions and idempotency for replay-sensitive endpoints.

**Acceptance obligation:** Add full compatibility checking and typed streaming/file response metadata; generated shapes do not runtime-validate arbitrary JSON.

### G24 — Frontend data architecture

**State:** PARTIAL. **Owner:** `frontend/src/platform/api/; frontend/src/platform/workspace/`.

**Decision:** TanStack Query with user/tenant/workspace keys; immutable tenant-scoped API client; explicit invalidation; mutations do not auto-retry.

**Acceptance obligation:** Run actual React integration tests for tenant switches, expired CSRF, network races and cache cancellation.

### G25 — Database architecture

**State:** IMPLEMENTED. **Owner:** `backend/migrations/; backend/app/platform/database.py`.

**Decision:** Concrete domain tables, constraints, explicit registry/tenant Alembic heads, bounded engine cache, no request-time DDL.

**Acceptance obligation:** Migrate and restore representative previous schemas; compare lock behavior under documented topology and production-like load.

### G26 — Mounted SQLite qualification

**State:** EXTERNAL. **Owner:** `backend/app/profiles/company/storage_probe.py; deploy/company-qualification.template.json`.

**Decision:** Diagnostic probe never grants safety approval. DELETE journal is a conservative supported profile, not a cure for S3 semantics.

**Acceptance obligation:** Require provider SQLite support plus topology and durability evidence; unsupported object/FUSE mounts remain blocked.

### G27 — Direct DB tooling

**State:** PARTIAL. **Owner:** `backend/app/tooling/work_items.py`.

**Decision:** Trusted same-host utilities reuse identity, permission, transaction and audit services rather than ad-hoc sqlite connections.

**Acceptance obligation:** Exercise real trusted job/API consumers and enforce filesystem access controls; raw DB access can bypass application authorization.

### G28 — File storage

**State:** PARTIAL. **Owner:** `backend/app/platform/attachments.py`.

**Decision:** Bounded attachments in tenant DB BLOBs for atomic metadata/content backup; safe names, MIME/magic validation and forced downloads.

**Acceptance obligation:** Add malware/CDR policy before accepting untrusted enterprise documents; large-file filesystem/object adapter remains unimplemented.

### G29 — Migrations, backup and recovery

**State:** PARTIAL. **Owner:** `backend/app/platform/backup.py; docs/RECOVERY.md`.

**Decision:** Explicit migration CLI, quiescent multi-database snapshots, hashes/integrity checks and isolated fresh-root restore.

**Acceptance obligation:** Perform company restore/redeploy drill, define RPO/RTO and encrypted off-host retention; APP-STOPPED token is operator acknowledgement, not a distributed lock.

### G30 — Import and export

**State:** PARTIAL. **Owner:** `backend/app/features/work_items/exchange.py`.

**Decision:** Versioned CSV, reversible formula escaping, bounded preview, fingerprint review and atomic import.

**Acceptance obligation:** Add XLSX, relationship-aware multi-entity snapshots, background imports and export audit policy where required.

### G31 — External integrations

**State:** DESIGNED. **Owner:** `docs/MASTER_DESIGN.md`.

**Decision:** Adapter boundary with typed results, origin allowlists, scoped secrets, timeout/retry/idempotency rules.

**Acceptance obligation:** Implement a real company-approved integration and replay/error tests; no integration provider is bundled.

### G32 — Background and scheduled work

**State:** DESIGNED. **Owner:** `docs/MASTER_DESIGN.md`.

**Decision:** Separate native worker publication when required; durable jobs, leases and fencing must match supported database semantics.

**Acceptance obligation:** Choose and prove company-compatible job execution; no fake timer loop advertised as durable scheduling.

### G33 — Realtime

**State:** DESIGNED. **Owner:** `docs/MASTER_DESIGN.md`.

**Decision:** Optional authenticated tenant-scoped event transport; default baseline uses query refresh rather than global broadcasts.

**Acceptance obligation:** Implement authorization on connect and each subscription, replay/reconnect policy and multi-instance delivery tests.

### G34 — Audit

**State:** PARTIAL. **Owner:** `backend/app/platform/audit.py; backend/migrations/tenant/0001_tenant.py`.

**Decision:** Actor/tenant/request-correlated changes written transactionally; SQLite triggers reject update/delete of audit rows.

**Acceptance obligation:** Define retention, export logging and tamper-evident external evidence; database owners can alter schema, so this is not WORM storage.

### G35 — Errors and diagnostics

**State:** IMPLEMENTED. **Owner:** `backend/app/platform/errors.py; frontend/src/platform/api/client.ts`.

**Decision:** Safe API error envelope, request IDs, bounded client response diagnostics, explicit configuration/bootstrap failures.

**Acceptance obligation:** Test failure kinds and prevent secrets in responses; full SysGrid support-bundle UX remains outside this implementation.

### G36 — Observability

**State:** PARTIAL. **Owner:** `backend/app/platform/middleware.py; backend/app/main.py`.

**Decision:** Request admission/logging, correlation IDs, health/readiness and safe diagnostics.

**Acceptance obligation:** Add operational metrics, latency histograms, traces, alerts and target PaaS log collection; configure service-level objectives.

### G37 — Security model

**State:** PARTIAL. **Owner:** `docs/SECURITY.md; backend/tests/test_security.py`.

**Decision:** Fail-closed production profile, server identity/membership, CSRF, explicit origins/hosts, bounded input, path constraints and revisions.

**Acceptance obligation:** Independent threat review and penetration tests; resolve actual identity/storage assumptions; no claim of ASVS conformance.

### G38 — Supply chain

**State:** BLOCKED. **Owner:** `backend/requirements.lock; frontend/package.json; .github/workflows/verify.yml`.

**Decision:** Exact backend dependency snapshot and candidate frontend pins; CI requires locks and high-severity advisory gates.

**Acceptance obligation:** Resolve/review frontend lock, install/scan dependencies, add hash-locked Python artifacts, SBOM/provenance and licensing review.

### G39 — Accessibility

**State:** BLOCKED. **Owner:** `frontend/tests/e2e/; frontend/src/platform/ui/`.

**Decision:** Native semantics, labels, keyboard/dialog source and Playwright axe test definitions exist.

**Acceptance obligation:** Run the built app plus manual keyboard/screen-reader/zoom testing; zero serious/critical axe findings alone does not certify WCAG.

### G40 — Performance

**State:** DESIGNED. **Owner:** `docs/MASTER_DESIGN.md`.

**Decision:** Bounded 50-row UI pages, 100-row bulk/import, 1 MB attachments and short serialized SQLite writes.

**Acceptance obligation:** Measure production-like bundle size, p95 latency, render responsiveness and memory under expected load; no benchmark claims from design limits.

### G41 — Browser and devices

**State:** BLOCKED. **Owner:** `frontend/playwright.config.ts; frontend/src/theme/`.

**Decision:** Desktop-first responsive CSS and Chromium test harness; browser support matrix is proposed, not certified.

**Acceptance obligation:** Qualify company-managed browser/version, Windows/macOS modifiers, 200% zoom and mobile layouts where required.

### G42 — Locale and time

**State:** PARTIAL. **Owner:** `backend/app/platform/schemas.py; frontend/src/generated/schema.ts`.

**Decision:** UTC serialization and Unicode validation; labels in app/feature definitions, English reference UI.

**Acceptance obligation:** Centralize UI date/number formatting and localization catalogs; define display timezone and DST behavior.

### G43 — Notifications

**State:** PARTIAL. **Owner:** `frontend/src/platform/ui/Notice.tsx`.

**Decision:** Transient success/error status notices only; no email/push/in-app inbox provider.

**Acceptance obligation:** Add accessible announcement timing/dismissal and optional provider-backed durable notifications with preferences.

### G44 — Flags and capabilities

**State:** PARTIAL. **Owner:** `backend/app/features/work_items/definition.py; backend/app/platform/policy.py`.

**Decision:** Workspace metadata and server permission registry; visible capabilities must not replace backend enforcement.

**Acceptance obligation:** Add typed runtime flag policy and validate capabilities against installed handlers to prevent advertised but missing features.

### G45 — Developer commands

**State:** IMPLEMENTED. **Owner:** `dev; scripts/`.

**Decision:** One dev entrypoint: setup/start/seed/contracts/architecture/verify/create/upgrade-plan/operator.

**Acceptance obligation:** Commands use explicit data roots, refuse destructive implicit resets and report missing prerequisites as blocked.

### G46 — Development environments

**State:** PARTIAL. **Owner:** `dev; scripts/e2e_runner.py; deploy/`.

**Decision:** Explicit localhost profile, isolated smoke/E2E data and separate production env examples.

**Acceptance obligation:** Qualify forwarded company dev origins and platform publisher behavior; do not copy development identity into production.

### G47 — Test architecture

**State:** PARTIAL. **Owner:** `evidence/verification/; backend/tests/; frontend/tests/`.

**Decision:** Executed backend/tooling/client/static-server/HTTP checks plus the React build, unit/typecheck and Playwright browser suite; company deployment and broader manual qualification remain separate.

**Acceptance obligation:** Run complete clean-install UI/API/security/browser suites plus company recovery and performance tests.

### G48 — Golden behavioral contracts

**State:** PARTIAL. **Owner:** `backend/tests/; scripts/check_architecture.py`.

**Decision:** Revision, CSV, authorization, storage, API and source-boundary tests protect several repeated failure classes.

**Acceptance obligation:** Add full SysGrid grid/overlay/lifecycle behavior suite and AST-based frontend rules; string checks are not exhaustive.

### G49 — Authoritative verification

**State:** PARTIAL. **Owner:** `scripts/verify.py`.

**Decision:** Single command records exact commands, logs, PASS/FAIL/BLOCKED and separates code readiness from deployment certification.

**Acceptance obligation:** Clean installation passes every code gate; any missing lock/tool is blocked, never quietly skipped.

### G50 — CI/CD

**State:** PARTIAL. **Owner:** `.github/workflows/verify.yml`.

**Decision:** Pinned-action CI executes backend/tools and exact frontend root with required lock and browser/security jobs.

**Acceptance obligation:** Run real PR CI, configure protected branches and artifact attestations; no remote workflow was executed in this delivery.

### G51 — Native PaaS adapters

**State:** EXTERNAL. **Owner:** `deploy/; frontend/server.mjs; backend/run.py`.

**Decision:** FastAPI app.main:app plus optional run.py; React dist or native Node server.mjs; explicit runtime JSON.

**Acceptance obligation:** Verify actual PaaS starting-file/root/runtime conventions, domains and persistence before publication.

### G52 — Codex workflow

**State:** IMPLEMENTED. **Owner:** `AGENTS.md; docs/CODEX.md`.

**Decision:** Local repository instructions identify editing boundaries, proofs and no automatic destructive operations.

**Acceptance obligation:** New agent follows the repository without claiming unrun tests; do not overwrite SysGrid control-room policy.

### G53 — Agent-friendly organization

**State:** PARTIAL. **Owner:** `frontend/src/; backend/app/; docs/recipes/`.

**Decision:** Small feature modules, local recipes, generated types and limited platform ownership.

**Acceptance obligation:** Observe real agent implementation tasks and context use; do not claim token savings without measurement.

### G54 — Architecture linting

**State:** PARTIAL. **Owner:** `scripts/check_architecture.py`.

**Decision:** Python AST and targeted TypeScript source checks enforce known dependency/identity/transport/storage constraints.

**Acceptance obligation:** Add full TypeScript AST rules and exception policy; test deliberate bypass attempts and false positives.

### G55 — Generators

**State:** PARTIAL. **Owner:** `scripts/template_tools.py`.

**Decision:** Fresh application generator with configuration overrides, no source mutation and managed-core hashes.

**Acceptance obligation:** Add feature/workspace/schema/migration generators only after second-domain patterns are validated.

### G56 — Documentation

**State:** IMPLEMENTED. **Owner:** `docs/; README.md`.

**Decision:** Local startup, customization, security, deployment, recovery, architecture decisions, recipes, evidence and scope ledger.

**Acceptance obligation:** Keep commands executable and add automated documentation-link/recipe tests as tooling matures.

### G57 — Neutral reference feature

**State:** PARTIAL. **Owner:** `backend/app/features/work_items/; frontend/src/features/work-items/`.

**Decision:** Real work-items backend and React source with CRUD, revisions, saved views, history, bulk, CSV and attachments.

**Acceptance obligation:** Build and browse the feature; complete grouping/context/compare parity and permission-lifecycle UX acceptance.

### G58 — Reference variants

**State:** PARTIAL. **Owner:** `tests/test_template_tools.py; frontend/src/theme/tokens.css`.

**Decision:** Three generated theme configurations retain identical core hashes.

**Acceptance obligation:** Implement a second domain and materially different shell; theme switches alone are not proof of radical product customizability.

### G59 — Exhaustive SysGrid file audit

**State:** INCOMPLETE. **Owner:** `docs/SYSGRID_EXTRACTION.md; SOURCE_PROVENANCE.json`.

**Decision:** Pinned branch/tree and selected high-value contracts were read; retained mapping records exactly this scope.

**Acceptance obligation:** Inventory and inspect every relevant source/test/guard with hashes and evidence; do not label a sampled review exhaustive.

### G60 — SysGrid behavior inventory

**State:** INCOMPLETE. **Owner:** `docs/SYSGRID_EXTRACTION.md`.

**Decision:** Monitoring common patterns are recorded from source; no live screenshots or whole-product behavior catalogue.

**Acceptance obligation:** Capture routed UX and tests against the pinned source for all target domains, including recent Project changes.

### G61 — SysGrid migration

**State:** INCOMPLETE. **Owner:** `docs/SYSGRID_MIGRATION.md`.

**Decision:** No changes were made to SysGrid; staged compatibility plan is documented.

**Acceptance obligation:** Migrate one real domain behind a switch, prove parity, then two distinct domains before declaring generality.

### G62 — Technical-debt cleanup

**State:** PARTIAL. **Owner:** `docs/ADRS.md`.

**Decision:** New core avoids giant modules, dual API types, global CSS overrides and root-package CI confusion.

**Acceptance obligation:** This does not repair current SysGrid in place; test actual migration and code ownership changes independently.

### G63 — Repository hygiene

**State:** PARTIAL. **Owner:** `.gitignore; scripts/template_tools.py`.

**Decision:** Ignore data/secrets/caches; tracked examples only; reviewed source/evidence separated.

**Acceptance obligation:** Add clean-checkout scans, owner-selected licensing and codeowners/protected branches in the target repository.

### G64 — Platform governance

**State:** DESIGNED. **Owner:** `docs/MASTER_DESIGN.md; docs/UPGRADING.md`.

**Decision:** Promote only proven repeated behavior; application quirks remain in features; version breaking public contracts.

**Acceptance obligation:** Assign maintainers and perform one reviewed upgrade/contribution cycle.

### G65 — Release certification

**State:** BLOCKED. **Owner:** `docs/RELEASE_STATUS.md; evidence/verification/verification.json`.

**Decision:** Review build is NOT_CERTIFIED; local evidence never authorizes company deployment.

**Acceptance obligation:** Close scope gaps, code gates and company evidence; independent approval tied to exact artifact digest.

### G66 — Home/cloud extension points

**State:** DESIGNED. **Owner:** `docs/MASTER_DESIGN.md`.

**Decision:** Identity/database/storage/deployment can be replaced at composition boundaries; no home profile implementation bundled.

**Acceptance obligation:** Implement and test OIDC/PostgreSQL/object storage only after company core proves itself; do not assume database dialect portability.

### G67 — Success metrics

**State:** DESIGNED. **Owner:** `docs/MASTER_DESIGN.md`.

**Decision:** Measure accepted-feature effort, context/usage, changed core files, regressions, build time and upgrade conflicts.

**Acceptance obligation:** Run comparable real tasks and publish observed results, not invented productivity percentages.

### G68 — Decision records

**State:** IMPLEMENTED. **Owner:** `docs/ADRS.md`.

**Decision:** Key choices, alternatives, limitations and proof obligations are retained.

**Acceptance obligation:** Keep decisions current when adapters, infrastructure or public contracts change.

## Sources and attribution

[S1] SQLite WAL: https://www.sqlite.org/wal.html
[S2] SQLite over networks: https://www.sqlite.org/useovernet.html
[S3] AWS Mountpoint filesystem scope: https://docs.aws.amazon.com/AmazonS3/latest/userguide/mountpoint.html
[S4] Python process environment: https://docs.python.org/3/library/os.html#os.environ
[S5] FastAPI sync/async routing: https://fastapi.tiangolo.com/async/
[S6] FastAPI generated clients: https://fastapi.tiangolo.com/advanced/generate-clients/
[S7] W3C native dialog technique: https://www.w3.org/WAI/WCAG22/Techniques/html/H102
[S8] WCAG 2.2: https://www.w3.org/TR/WCAG22/
[S9] Codex repository instructions: https://developers.openai.com/codex/guides/agents-md/

SysGrid source evidence is identified separately in SOURCE_PROVENANCE.json and SYSGRID_EXTRACTION.md. Upstream links provide design rationale, not attestation that this implementation conforms to every standard.
