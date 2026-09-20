# Verification contract

## Native widget layer

Run `python3 dev test-lab` after installing Python test dependencies, a TypeScript compiler and Chromium/Playwright. Default `http` mode starts a real ephemeral local web server. This command checks strict TypeScript and shipped-artifact parity, pure model tests, HTTP static-server behavior, catalog drift and real Chromium widget interactions. Results include source hashes and logs.

The current evidence uses the HTTP-mode Lab harness and the React browser runner with disposable loopback services. The harness loads exact compiled code and CSS and separately tests HTTP serving; it does not certify deployment or full accessibility.

Useful independent commands:

```bash
python3 scripts/check_lab_build.py
node --test experience-lab/tests/model.test.mjs
python3 -m pytest -q tests/test_lab_server.py
python3 scripts/catalog.py --check
python3 scripts/catalog.py --check --release
```

The last command is the release contract for the generated 605-entry generic family registry. Pure algorithms cover schedule validation/cycles, rack collisions/capacity/power, wafer yield, carrier slot uniqueness, traveler state rules, floor placement, model bounds, CSV formula injection, HTML escaping and presentation options. Browser tests exercise interactions and states rather than only screenshots.

## React/FastAPI application

CHG-35 uses `contracts/performance-regression.json` as the only authority for
the owned pure-algorithm, platform data-volume and browser/AG Grid scale
workloads, representative sizes, structural invariants and generous
regression ceilings. `scripts/performance_check.py`,
`scripts/performance_stress.py` and `frontend/tests/e2e/performance.spec.ts`
consume that contract; `scripts/performance_results.py` fails closed on stale,
unknown, duplicate or missing results. The 100k/50 server-page fixture proves
the production paging boundary. The separate 5000-loaded-row fixture is
synthetic/test-only and exercises the shared `StandardDataGrid`'s actual AG
Grid virtualization, recycling, deep selection/keyboard behavior and sorting.
`GroupedSemanticGrid` remains a non-virtualized semantic table bounded by the
server-returned page and is not certified as virtualized.

`python3 dev setup` creates the repository-local `backend/.venv` from the reviewed locks and installs the frontend lock. Run it before `python3 dev verify` or `python3 dev verify-release`; backend gates refuse an ambient interpreter so local verification uses the same environment contract as CI. The verifier checks backend, tooling, architecture, generated API contracts, client transport logic, Node static publisher and real Uvicorn HTTP requests. It then requires the installed/locked React dependency tree, full TypeScript, unit tests, production build, browser/a11y, dependency advisories, catalog completion and an isolated exact-candidate clean-install proof. On Linux, that proof is a portable candidate gate and macOS-specific qualification is recorded as `BLOCKED`; on Darwin it can provide the macOS qualification. Company identity, mounted-storage and deployment checks remain explicitly external.

Missing tooling is BLOCKED, never PASS. A missing required catalog implementation is FAIL. Its nonzero exit must not be weakened merely to get a green badge.

## Operational reliability qualification

`contracts/operational-reliability.json` is the canonical scenario contract. Run
`python3 dev operations` to exercise its repository scenarios against disposable
local resources: fail-closed startup/configuration, liveness/readiness and safe
database envelopes, attachment cleanup, durable retry/heartbeat/fencing,
webhook refusal/retry, invalid restore refusal and diagnostic redaction. The
aggregate at `evidence/current/operations/qualification.json` is bound to the
candidate checkout, executable-source commit/digest and contract hash. Missing
or reordered scenarios, skipped faults, stale source/contract identity,
sensitive evidence fields or any production claim make the aggregate fail
closed. A repository PASS is not authentic company operations evidence and
leaves the final CompanyQualification operations gate `BLOCKED_EXTERNAL`.

## Visual and accessibility evidence

`evidence/current/browser` contains current browser evidence. Light/dark renderings, key interactions, focus guards, mobile overflow, axe checks across registered workspaces, keyboard smoke, 200%/400% zoom, reduced motion and high contrast were exercised. This is not a WCAG certification, independent screen-reader qualification or non-Chromium engine certification.

CHG-34 adds one canonical state registry at `frontend/tests/e2e/ui-state-matrix.json`. Its applicable rows are the only source for deterministic UIQA browser IDs, and `scripts/check_ui_state_matrix.py` fails closed on duplicate/unknown IDs, missing executable coverage, missing required dimensions or result drift. The established `frontend/tests/e2e/uiqa.spec.ts` remains the executable Playwright + axe path; it writes browser-computed result metadata to `evidence/current/uiqa/ui-state-matrix-results.json` and rendered artifacts under `evidence/current/uiqa/rendered/`. Coverage includes normal/loading/empty/error/permission/selection states where applicable, light/dark themes, high contrast/forced-colors, desktop/narrow layouts, precise 320 CSS px reflow evidence, reduced motion, keyboard semantics and focus recovery. Storybook remains a deterministic component/state workbench and does not replace the rendered browser gate. Local UIQA evidence strengthens repository code readiness but cannot pass the external company/profile `ui_accessibility` qualification gate.

## Frontend bundle budget

The application uses route-level dynamic imports for registered workspaces and keeps the production Vite budget at 1.2 MB per minified chunk; the current application build emits no size warning. Storybook has a separate 1.2 MB tooling budget because its generated docs/a11y iframe is intentionally aggregated and is not shipped with the application.

## CI

The independent Lab workflow runs on Linux and macOS and defaults to HTTP-mode browser tests. It is supplied configuration, not an already completed CI run. The full platform workflow creates `backend/.venv` and invokes the verifier through that interpreter. Its clean-install proof clones the current checkout's exact `HEAD`, never a stale remote `main`; a Lab-only green job does not certify the platform.

## Backend test-client compatibility

The test requirements pin `httpx2==2.12.0`, together with its exact transitive lock entries, for compatibility with the installed FastAPI/Starlette test client. Use the project venv for backend checks; the release verifier runs `scripts/backend_test_runner.py`, which assigns the sorted backend test files to four deterministic parallel shards and merges their JUnit output. This keeps the complete 236-test suite inside the local gate budget without changing test selection or assertions. The venv run completes without the former `StarletteDeprecationWarning`; an unrelated system Python that lacks `httpx2` may still emit Starlette's upstream fallback warning. This is a strictly upstream fallback warning, not a repository-actionable failure.

```bash
backend/.venv/bin/python scripts/backend_test_runner.py --output evidence/current/full-stack/backend-junit.xml
```

## Evidence durability

The repository checkpoint is generated with `python3 scripts/generate_checkpoint_manifest.py` and checked with `python3 scripts/generate_checkpoint_manifest.py --check`. Release verification uses `./dev verify-release`, which refreshes the pre-verification snapshot, verifies the exact executable source, then runs `scripts/finalize_release.py` to bind the final release identity, regenerate the broader checkpoint and check it. Run `python3 scripts/checkpoint.py <label>` after meaningful changes. Each atomic ZIP includes source, compiled Lab artifacts, documentation and evidence with SHA-256 hashes. Dependencies, private keys, database files, fonts and local credentials are excluded. Extract the ZIP and verify it before delivery; retain code, not just screenshots. Source is authoritative; prior test results expire when their inputs change.
