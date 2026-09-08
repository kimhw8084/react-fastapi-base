# Verification contract

## Native widget layer

Run `python3 dev test-lab` after installing Python test dependencies, a TypeScript compiler and Chromium/Playwright. Default `http` mode starts a real ephemeral local web server. This command checks strict TypeScript and shipped-artifact parity, pure model tests, HTTP static-server behavior, catalog drift and real Chromium widget interactions. Results include source hashes and logs.

The current execution used `python3 scripts/verify_lab.py --mode in_memory`. The managed browser blocked localhost navigation. The harness loads exact compiled code and CSS without relaxing browser policy; it tests widgets, not browser networking. This limitation is recorded in the report and does not count as a React or deployment pass.

Useful independent commands:

```bash
python3 scripts/check_lab_build.py
node --test experience-lab/tests/model.test.mjs
python3 -m pytest -q tests/test_lab_server.py
python3 scripts/catalog.py --check
python3 scripts/catalog.py --check --release
```

The last command intentionally fails while required scope remains non-stable. Pure algorithms cover schedule validation/cycles, rack collisions/capacity/power, wafer yield, carrier slot uniqueness, traveler state rules, floor placement, model bounds, CSV formula injection, HTML escaping and presentation options. Browser tests exercise interactions and states rather than only screenshots.

## React/FastAPI application

`python3 dev verify` checks backend, tooling, architecture, generated API contracts, client transport logic, Node static publisher and real Uvicorn HTTP requests. It then requires the installed/locked React dependency tree, full TypeScript, unit tests, production build, browser/a11y, dependency advisories, catalog completion, Mac certification and environment gates.

Missing tooling is BLOCKED, never PASS. An incomplete required catalog is FAIL. Its nonzero exit is intentional and must not be weakened merely to get a green badge.

## Visual and accessibility evidence

`evidence/current/browser` contains actual widget screenshots captured during tests. Light/dark renderings, key interactions, focus guards and mobile overflow were exercised. Automated axe, all contrast/zoom requirements, manual screen-reader review, complete keyboard coverage and non-Chromium engines are not yet certified.

## CI

The independent Lab workflow runs on Linux and macOS and defaults to HTTP-mode browser tests. It is supplied configuration, not an already completed CI run. The separate full-platform workflow keeps the frontend lock and full scope as mandatory gates. A Lab-only green job does not certify the platform.

## Evidence durability

Run `python3 scripts/checkpoint.py <label>` after meaningful changes. Each atomic ZIP includes source, compiled Lab artifacts, documentation and evidence with SHA-256 hashes. Dependencies, private keys, database files, fonts and local credentials are excluded. Extract the ZIP and verify it before delivery; retain code, not just screenshots. Source is authoritative; prior test results expire when their inputs change.
