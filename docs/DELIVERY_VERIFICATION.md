# Delivery verification — react-fastapi-base 1.0.0-rc.1

**The standalone Experience Lab is runnable. The complete production platform is not certified.**

## Actual executed tests

| Check | Result |
|---|---:|
| FastAPI/backend | 103 passed |
| Chromium widget/browser cases | 99 passed |
| Pure engineering model cases | 39 passed |
| Python generation/static-server tooling | 13 passed |
| Node static publisher | 9 passed |
| Pure TypeScript API/runtime cases | 10 passed |
| Strict TypeScript/native artifact parity | 36 JS/declaration files matched |
| Current source against verification hashes | 203 matched; zero drift |

23 interactive widget families are implemented provisionally. 605 required scope entries are retained; these are components, variants and platform services, not an implemented-component count.

The current full platform gate records the executed local results in `evidence/current/full-stack/verification.json`. The catalog completeness check deliberately fails while required entries remain provisional. React/Storybook, dependency advisory scans, backend tests, Lab/browser checks and the bounded accessibility workflow now execute locally; full scope, manual accessibility, stress, fresh-clone, macOS and company qualification remain mandatory.

The Chromium suite used an explicitly identified in-memory exact-artifact loader because managed browser policy blocks localhost navigation here. Separate tests exercised real HTTP static serving and Uvicorn. No browser security policy was changed. These results do not prove React integration, browser HTTP/CSP behavior, corporate identity, mounted storage or complete WCAG compliance.

The current source and compiled Lab are delivered together, with a ZIP manifest and checksum. No SysGrid source modification, remote commit, company deployment or production database operation occurred.

## Start the delivered Lab

```bash
cd react-fastapi-base
python3 dev lab
```

Then open `http://127.0.0.1:4173`. This uses synthetic local models. No npm setup is required to view the Lab. Read README.md and docs/MAC_QUICKSTART.md for the separate full React/FastAPI path and the unresolved release gates.

Full logs: `evidence/current/full-stack/`; native browser details: `evidence/current/full-stack/native-lab/`; screenshots: `evidence/current/browser/`.
