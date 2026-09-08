# Release status — react-fastapi-base 1.0.0-rc.1

## Decision

**NOT COMPLETE.** This is a reproducible implementation review build, not a production release. The exact subsystem status is maintained in [v1-completion-status.json](v1-completion-status.json); source, migrations, generated contracts, tests, and executed evidence take precedence over historical prose.

## Verified in this checkout

- Frontend lockfile, `npm ci`, TypeScript, unit tests, production build, Storybook build, and actual React browser workflows.
- FastAPI backend suite: 179 tests passing on the security-updated dependency set, including typed integrations, statistical parity, fenced durable jobs, membership-scoped saved views, webhook delivery history and reviewed XLSX exchange.
- Isolated clean-clone Mac certification: setup, contracts, architecture, catalog release check, backend tests, frontend typecheck/build, Storybook and React E2E all passed with cache isolation.
- Generated contract check, architecture lint, source security checks, owned algorithm performance checks, Lab build, and Lab HTTP/browser tests.
- Native and React surfaces use synthetic/disposable data only.

## Remaining release blockers

- The 605-entry catalog now passes its generic family-level certification contract; domain-specific production qualification remains tracked separately in the completion matrix.
- Upgrade fixture and seven generated reference applications pass disposable migration/contract/frontend test/build proofs; feature-specific domain depth remains tracked separately in the completion matrix.
- Deterministic stress proofs pass 100k table/wafer/observability/SPC-scale algorithms, 5k planning tasks, large graph/rack datasets and dashboard layout inputs; browser DOM/memory profiling remains open.
- Full accessibility requires major-screen axe coverage plus manual keyboard, zoom, high-contrast, and VoiceOver evidence.
- Full performance requires the specified 100k-row and large graph/rack/wafer/log/SPC stress runs.
- Independent generator/reference-app proofs remain to be completed.
- Saved views now support explicit tenant teams with server-enforced membership and a conflict-resolution recovery action; favorites/defaults and offline reconciliation remain open.
- The System workspace now exposes team creation/member management and has an actual Playwright workflow covering the server-enforced team scope.
- Webhook deliveries now persist attempt/status/response history and expose bounded admin history in the System workspace; external dispatch remains job-worker/provider infrastructure.
- Work-item exchange now supports dependency-free XLSX export, preview and atomic reviewed import with formula-cell rejection; multi-entity relationship snapshots remain open.
- Company identity, mounted-storage, deployment/redeploy, and company backup/restore remain external execution gates; ordinary Mac execution and isolated clean-clone certification are now evidenced separately.

## Evidence policy

Reports under `evidence/current/` are generated from the current source. Historical reports remain under historical directories and are not release proof. A passing local test does not certify the company environment, SEMI compliance, WCAG conformance, or production safety.
