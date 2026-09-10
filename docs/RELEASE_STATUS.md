# Release status — react-fastapi-base 1.0.0-rc.3

## Decision

**V1 LOCAL CODE COMPLETE — COMPANY QUALIFICATION PENDING.** All locally achievable V1 contracts in [v1-completion-status.json](v1-completion-status.json) are implemented and have current source-backed verification. This is not a company production certificate.

## Current local proof

- Backend: 230 tests passed across the deterministic four-shard runner; generated contracts, migrations, architecture checks, security-source checks and owned statistical/performance checks passed.
- Frontend: locked `npm ci`, TypeScript, 16 Vitest files / 40 tests, production build, Storybook build and 12 Playwright workflows passed.
- Browser proof covers create/reload/dossier tabs, dirty navigation, team saved views, administration events/teams, every registered workspace, mobile keyboard/axe, a 100k logical-row bounded table, and major surfaces at 200%/400% zoom with reduced motion and high contrast. Tested workflows reported no browser console errors or page errors.
- Platform proof covers server-owned computed fields, generic relationship explorers, saved-view schema reconciliation/conflict recovery, universal dossier compare, deterministic attachment scanning, typed integration adapters, and relationship-set stress.
- `scripts/catalog.py --check --release` passes all 605 retained catalog entries without wrapper-only certification.
- Seven generated reference applications pass their migration, contract, frontend test/build and source-integrity proofs. The upgrade fixture passes plan, conflict-safe apply, migration, build/tests, rollback and integrity comparison.
- Deterministic performance stress passes the table, planning, graph, rack, wafer, observability, dashboard and SPC workloads. The isolated clean-clone macOS gate passes without reusing the working tree's virtualenv, node modules or caches.
- RC.2 hardens object-inclusive backup/restore, fails closed when production uploads have no malware scanner, renews long-running job leases, refreshes the deterministic source manifest, clarifies the historical requirements ledger, and makes archived/viewer dossier comments read-only.
- RC.3 centrally enforces the attachment upload policy for every caller, binds object export to the copied snapshot database, rejects archived comment deletion server-side, and reconciles the supported Python runtime documentation.

Current machine-readable evidence is under `evidence/current/`, especially [verification.json](../evidence/current/full-stack/verification.json), [backend-junit.xml](../evidence/current/full-stack/backend-junit.xml), [object-restore.json](../evidence/current/recovery/object-restore.json), [browser-e2e-accessibility.log](../evidence/current/full-stack/browser-e2e-accessibility.log), [stress.json](../evidence/current/performance/stress.json), [reference-apps.json](../evidence/current/release/reference-apps.json), and [fresh-clone-macos.json](../evidence/current/full-stack/fresh-clone-macos.json).

## External qualification only

- Real company AccessKey multi-user topology and identity isolation.
- Provider-mounted SQLite locking, journal, durability, redeploy persistence and backup/restore qualification.
- Company frontend/backend publication, ingress, restart and redeploy drill.
- Company-operated backup/restore and recovery drill.

Optional authenticated realtime push, enterprise malware/CDR provider selection, independent penetration testing and non-Chromium/manual screen-reader qualification are not misrepresented as local production certification or local release blockers.

## Evidence policy

Reports under `evidence/current/` are generated from the current source and carry commit, timestamp, command, exit code, environment and hashes. Historical reports remain under historical directories and are not release proof. Local success does not certify company infrastructure, SEMI compliance, WCAG conformance, or production safety.
