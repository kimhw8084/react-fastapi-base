# macOS quickstart — 1.0.0-rc.19

This is a portable launch procedure. The exact-candidate clean-clone proof and reusable-platform qualification are repository evidence; neither is a company deployment certificate.

## View the implemented application

1. Unpack the exact RC.17 repository checkout into a new folder, separate from SysGrid.
2. Open Terminal in the resulting `react-fastapi-base` folder.
3. Check `python3 --version` (3.11–3.14 for the full React/FastAPI path).
4. Run `python3 dev lab`.
5. Open `http://127.0.0.1:4173` in your browser.

Use `python3 dev lab --port 4174` if 4173 is occupied. It refuses an occupied port and never kills another application. Ctrl+C stops the server. No database file is opened; no directory is erased or seeded.

Directly double-clicking index.html is not the supported path because browsers restrict local JavaScript module loading. Use the bundled localhost server.

## Explore the main examples

`#/tables`, `#/boards`, `#/gantt`, `#/calendar`, `#/rack`, `#/wafer`, `#/carrier`, `#/traveler`, `#/floorplan`, `#/process`, `#/topology`, `#/traces`, `#/windows`, `#/themes`.

Cmd+K opens navigation search. The toolbar switches light/dark mode, state, read-only behavior and viewport preview. Theme Studio changes actual shared presentation and exports a non-secret appearance configuration.

## Develop the native widget layer

Use Node 22 and the TypeScript compiler version recorded in the verification report (5.8.3 for the shipped artifacts). A compiler is not required just to view the Lab.

```bash
npm install --global typescript@5.8.3
python3 dev lab-build
```

After changing registry/source, run `python3 dev catalog`. Do not hand-edit compiled JS. `scripts/check_lab_build.py` verifies its parity with TypeScript source.

## Run the widget tests

Use a Python environment with `experience-lab/requirements-test.txt` installed and install Playwright's browser:

```bash
python3 -m venv .lab-venv
.lab-venv/bin/python -m pip install -r experience-lab/requirements-test.txt
.lab-venv/bin/python -m playwright install chromium
.lab-venv/bin/python scripts/verify_lab.py
python3 dev test-lab --mode http
```

The default browser mode starts a real ephemeral localhost server. The test suite does not alter company browser policies. Tests use disposable fixtures and never company databases.

## Full React/FastAPI host

The backend contract is Python `>=3.11,<3.15`; current release evidence records the exact runner used. Node 22.12+ is the target frontend toolchain. `python3 dev setup`, `python3 dev seed-demo`, and `python3 dev start` are the implemented commands. Dependencies require registry access. The React dependency tree, build, and isolated exact-candidate clean-clone flow are current evidence. This is separate from the immediately runnable Lab.

The reusable-platform release gate is `python3 dev verify-release`; it writes `evidence/current/reuse/qualification.json` and keeps company identity, storage, deployment, operations and production readiness external. There is no implemented `./dev doctor` or `./dev start --production` command. See `python3 dev --help` for actual capabilities.
