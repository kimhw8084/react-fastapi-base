# Release status — react-fastapi-base 1.0.0-rc.1

## Decision

**NOT COMPLETE.** This is a reproducible implementation review build, not a production release. The exact subsystem status is maintained in [v1-completion-status.json](v1-completion-status.json); source, migrations, generated contracts, tests, and executed evidence take precedence over historical prose.

## Verified in this checkout

- Frontend lockfile, `npm ci`, TypeScript, unit tests, production build, Storybook build, and actual React browser workflows.
- The operational table now has a reusable advanced-filter/multi-sort builder, generated adapters and generated backend routers serialize/decode that state consistently, and Work Items prove a bounded server-owned rich-query plus fingerprinted all-matching bulk contract; heavy browser stress remains open.
- FastAPI backend suite: count is refreshed by the final release gate; it includes typed integrations, statistical parity, fenced durable jobs, membership-scoped saved views, webhook delivery history, reviewed XLSX exchange, storage adapter safety, rack constraints, and engineering-pack parity fixtures.
- Isolated clean-clone Mac certification: setup, contracts, architecture, catalog release check, backend tests, frontend typecheck/build, Storybook and React E2E all passed with cache isolation.
- Generated contract check, architecture lint, source security checks, owned algorithm performance checks, Lab build, and Lab HTTP/browser tests.
- Native and React surfaces use synthetic/disposable data only.

## Remaining release blockers

- The 605-entry catalog now passes its generic family-level certification contract; domain-specific production qualification remains tracked separately in the completion matrix.
- Upgrade fixture and seven generated reference applications pass disposable migration/contract/frontend test/build proofs; feature-specific domain depth remains tracked separately in the completion matrix.
- Deterministic stress proofs pass 100k table/wafer/observability/SPC-scale algorithms, 5k planning tasks, large graph/rack datasets and dashboard layout inputs; browser DOM/memory profiling remains open.
- Full accessibility requires major-screen axe coverage plus manual keyboard, zoom, high-contrast, and VoiceOver evidence.
- The specified deterministic 100k-row and large graph/rack/wafer/log/SPC stress runs pass; browser DOM/memory profiling and repeated-listener leak checks remain.
- Generator and reference-app proofs are current release evidence; future generator changes must keep those proofs green.
- Saved views now support explicit tenant teams with server-enforced membership, favorites/defaults with scoped default arbitration, and a conflict-resolution recovery action; offline/local reconciliation and broader browser conflict coverage remain open.
- The System workspace now exposes team creation/member management and has an actual Playwright workflow covering the server-enforced team scope.
- Webhook deliveries now persist attempt/status/response history and expose bounded admin history in the System workspace; external dispatch remains job-worker/provider infrastructure.
- Work-item exchange now supports dependency-free XLSX and versioned JSON export, preview and atomic reviewed import with formula-cell rejection; multi-entity relationship snapshots and large background imports remain open.
- A tenant-scoped storage adapter boundary now provides safe atomic local-filesystem and deterministic in-memory implementations, and both feature and generic dossier attachment paths use object-key-backed metadata with a scanner/CDR hook; provider implementation and company-mounted qualification remain open.
- Company identity, mounted-storage, deployment/redeploy, and company backup/restore remain external execution gates; ordinary Mac execution and isolated clean-clone certification are now evidenced separately.
- Rack optional PDU/power/thermal/weight constraints, graph editing history/layout actions, and semiconductor/software metric parity helpers are implemented and tested; their large-scale browser/stress proofs remain open.

## Evidence policy

Reports under `evidence/current/` are generated from the current source. Historical reports remain under historical directories and are not release proof. A passing local test does not certify the company environment, SEMI compliance, WCAG conformance, or production safety.
