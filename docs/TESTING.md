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

`python3 dev verify` checks backend, tooling, architecture, generated API contracts, client transport logic, Node static publisher and real Uvicorn HTTP requests. It then requires the installed/locked React dependency tree, full TypeScript, unit tests, production build, browser/a11y, dependency advisories, catalog completion and isolated Mac certification. Company identity, mounted-storage and deployment checks remain explicitly external.

Missing tooling is BLOCKED, never PASS. A missing required catalog implementation is FAIL. Its nonzero exit must not be weakened merely to get a green badge.

## Visual and accessibility evidence

`evidence/current/browser` contains current browser evidence. Light/dark renderings, key interactions, focus guards, mobile overflow, axe checks across registered workspaces, keyboard smoke, 200%/400% zoom, reduced motion and high contrast were exercised. This is not a WCAG certification, independent screen-reader qualification or non-Chromium engine certification.

## Frontend bundle budget

The application uses route-level dynamic imports for registered workspaces and keeps the production Vite budget at 1.2 MB per minified chunk; the current application build emits no size warning. Storybook has a separate 1.2 MB tooling budget because its generated docs/a11y iframe is intentionally aggregated and is not shipped with the application.

## CI

The independent Lab workflow runs on Linux and macOS and defaults to HTTP-mode browser tests. It is supplied configuration, not an already completed CI run. Local release verification is authoritative for this task; a Lab-only green job does not certify the platform.

## Backend test-client compatibility

The test requirements pin `httpx2==2.12.0`, together with its exact transitive lock entries, for compatibility with the installed FastAPI/Starlette test client. Use the project venv for backend checks; the release verifier runs `scripts/backend_test_runner.py`, which assigns the sorted backend test files to four deterministic parallel shards and merges their JUnit output. This keeps the complete 236-test suite inside the local gate budget without changing test selection or assertions. The venv run completes without the former `StarletteDeprecationWarning`; an unrelated system Python that lacks `httpx2` may still emit Starlette's upstream fallback warning. This is a strictly upstream fallback warning, not a repository-actionable failure.

```bash
backend/.venv/bin/python scripts/backend_test_runner.py --output evidence/current/full-stack/backend-junit.xml
```

## Evidence durability

Run `python3 scripts/checkpoint.py <label>` after meaningful changes. Each atomic ZIP includes source, compiled Lab artifacts, documentation and evidence with SHA-256 hashes. Dependencies, private keys, database files, fonts and local credentials are excluded. Extract the ZIP and verify it before delivery; retain code, not just screenshots. Source is authoritative; prior test results expire when their inputs change.
