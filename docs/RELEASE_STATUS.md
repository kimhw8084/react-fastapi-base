# Release status — react-fastapi-base 1.0.0-rc.1

## Decision

**NOT COMPLETE.** This is a reproducible implementation review build, not a production release. The exact subsystem status is maintained in [v1-completion-status.json](v1-completion-status.json); source, migrations, generated contracts, tests, and executed evidence take precedence over historical prose.

## Verified in this checkout

- Frontend lockfile, `npm ci`, TypeScript, unit tests, production build, Storybook build, and actual React browser workflows.
- FastAPI backend suite: 173 tests passing on the security-updated dependency set, including the typed integration boundary.
- Isolated clean-clone Mac certification: setup, contracts, architecture, catalog release check, backend tests, frontend typecheck/build, Storybook and React E2E all passed with cache isolation.
- Generated contract check, architecture lint, source security checks, owned algorithm performance checks, Lab build, and Lab HTTP/browser tests.
- Native and React surfaces use synthetic/disposable data only.

## Remaining release blockers

- The 605-entry catalog now passes its generic family-level certification contract; domain-specific production qualification remains tracked separately in the completion matrix.
- Advanced grid/server-scale, graph, planning, dashboard, statistical, semiconductor, software, administration, and upgrade capabilities remain partial in the completion matrix.
- Full accessibility requires major-screen axe coverage plus manual keyboard, zoom, high-contrast, and VoiceOver evidence.
- Full performance requires the specified 100k-row and large graph/rack/wafer/log/SPC stress runs.
- Independent generator/reference-app proofs remain to be completed.
- Company identity, mounted-storage, deployment/redeploy, and company backup/restore remain external execution gates; ordinary Mac execution and isolated clean-clone certification are now evidenced separately.

## Evidence policy

Reports under `evidence/current/` are generated from the current source. Historical reports remain under historical directories and are not release proof. A passing local test does not certify the company environment, SEMI compliance, WCAG conformance, or production safety.
