# Delivery verification — react-fastapi-base 1.0.0-rc.17

**The local code gates are green. The complete production platform is not certified for company deployment.**

RC.17's repository deployment proof is recorded in
`evidence/current/deployment/qualification.json`. It proves separate frontend
and backend publishers only; the final company deployment gate remains
`BLOCKED_EXTERNAL`.

## Actual executed tests

CHG-34 UI accessibility evidence is immutable historical evidence in
`evidence/current/release/CHG-34-ui-accessibility.json`. Current RC.17
repository readiness is recorded in
`evidence/current/release/rc17-readiness-matrix.json`. The independent
deployment qualification is recorded in
`evidence/current/deployment/qualification.json`. CHG-35 performance
qualification is recorded in
`evidence/current/performance/qualification.json` and
`evidence/current/release/CHG-35-performance-virtualization.json`. CHG-32
configuration-contract evidence remains immutable historical evidence in
`evidence/current/release/CHG-32-configuration-contract.json`. RC.17
reusable-platform qualification is recorded in `evidence/current/reuse/qualification.json`,
and repository storage qualification is recorded in
`evidence/current/storage/qualification.json`. The exact base for API
compatibility is `a5eb5a4d84695e80defe0d1f24679f6557c79c5f`.

| Check | Result |
|---|---:|
| FastAPI/backend | PASS; current deterministic backend suite in `evidence/current/full-stack/backend-junit.xml` |
| Frontend unit/typecheck/build | PASS |
| React browser workflows | PASS; 27 Playwright cases including 13 canonical CHG-34 UIQA rows, preserved UIQA regressions, and two CHG-35 performance cases |
| Storybook build | PASS |
| Experience Lab | PASS; current machine-readable report |
| Contracts/configuration/architecture/security/performance | PASS; configuration contract covers 18 backend, 2 publisher and 4 browser keys |
| API compatibility | PASS; Git-resolved base `a5eb5a4d84695e80defe0d1f24679f6557c79c5f`; API major/revision unchanged |
| Repository storage qualification | PASS locally; conservative filesystem/SQLite/object recovery contract only; final company storage remains `BLOCKED_EXTERNAL` |
| Catalog release contract | PASS; 605 generic family entries |
| Exact-candidate clean-install proof | PASS; setup through React E2E, with macOS qualification PASS on the current Darwin runner |
| Reusable-platform aggregate | PASS; canonical source-bound clean-consumer, reference-app, upgrade/rollback and documentation reconciliation |

23 interactive widget families and 605 generic catalog variants/platform entries are registered. Catalog certification proves reusable family contracts and rendering coverage; domain-specific maturity remains recorded in the completion matrix.

The current full platform gate records executed results in `evidence/current/full-stack/verification.json`. All verifier-owned code gates pass. On Linux, the same clean-install proof is recorded as the portable `candidate-fresh-install` code gate while macOS-specific qualification is truthfully `BLOCKED`; the current Darwin run provides the macOS qualification. The object-inclusive recovery fixture is recorded in `evidence/current/recovery/object-restore.json`. Company identity, mounted-storage semantics and real deployment remain external. The generated-app and upgrade proofs are current release evidence.

The React browser suite uses disposable local services and dynamically allocated loopback ports. The native Lab suite separately exercises exact compiled artifacts and HTTP serving. These results do not prove corporate identity, mounted storage or complete WCAG compliance.

The current source and compiled Lab are delivered together, with a ZIP manifest and checksum. No SysGrid source modification, remote commit, company deployment or production database operation occurred.

RC.11 contains the final CompanyQualification contract and source-bound readiness
matrix. RC.10 CHG-32 configuration/secrets evidence remains immutable historical
evidence. RC.9 CHG-31 API
compatibility evidence and RC.8 CHG-27 profile-contract evidence remain
historical for their exact sources, as do RC.7 UIQA and RC.6 evidence.

## Start the delivered Lab

```bash
cd react-fastapi-base
python3 dev lab
```

Then open `http://127.0.0.1:4173`. This uses synthetic local models. No npm setup is required to view the Lab. Read README.md and docs/MAC_QUICKSTART.md for the separate full React/FastAPI path and the unresolved release gates.

Full logs: `evidence/current/full-stack/`; native browser details: `evidence/current/full-stack/native-lab/`; screenshots: `evidence/current/browser/`.
