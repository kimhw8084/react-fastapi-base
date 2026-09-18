# Delivery verification — react-fastapi-base 1.0.0-rc.12

**The local code gates are green. The complete production platform is not certified for company deployment.**

## Actual executed tests

CHG-34 UI accessibility evidence is recorded in
`evidence/current/release/CHG-34-ui-accessibility.json` and
`evidence/current/release/rc12-readiness-matrix.json`. CHG-32
configuration-contract evidence remains immutable historical evidence in
`evidence/current/release/CHG-32-configuration-contract.json`. The exact
base for API compatibility is the integrated main commit supplied for this
branch: `1de9cfae29450990d201785f35992c72ff0d0684`.

| Check | Result |
|---|---:|
| FastAPI/backend | PASS; current deterministic backend suite in `evidence/current/full-stack/backend-junit.xml` |
| Frontend unit/typecheck/build | PASS |
| React browser workflows | PASS; 26 Playwright cases including 13 canonical CHG-34 UIQA rows and preserved UIQA regressions |
| Storybook build | PASS |
| Experience Lab | PASS; current machine-readable report |
| Contracts/configuration/architecture/security/performance | PASS; configuration contract covers 18 backend, 2 publisher and 4 browser keys |
| API compatibility | PASS; Git-resolved base `1de9cfae29450990d201785f35992c72ff0d0684`; API major/revision unchanged |
| Catalog release contract | PASS; 605 generic family entries |
| Exact-candidate clean-install proof | PASS; setup through React E2E, with macOS qualification PASS on the current Darwin runner |

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
