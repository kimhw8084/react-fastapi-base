# react-fastapi-base

`1.0.0-rc.1` — reproducible review build; not production certified.

This repository is a React/FastAPI engineering-workstation template. It contains a typed React application, a FastAPI/SQLite backend with explicit migrations, generated API contracts, reusable workspace primitives, domain packs, generators, and the compiled Experience Lab. SysGrid is read-only behavioral reference; it is not modified or bundled as copied application code.

## Run locally

The zero-install Experience Lab uses synthetic data:

```bash
python3 dev lab
```

Open `http://127.0.0.1:4173`. For the full React/FastAPI path, use a Python 3.13+ environment and Node 22.12+ in the Node 22 line:

```bash
python3 dev setup
python3 dev seed-demo
python3 dev start
```

The local profile uses disposable demo identity and data. Startup does not create, reset, or migrate production data. The company profile fails closed until operator qualification is supplied.

## Current implementation

The backend includes canonical feature modules for work items, projects, racks, equipment, Knowledge, Investigation, Risk, Research, Diagram Designer, Planning, analytics/SPC, semiconductor records, software delivery/observability, and platform administration services. The frontend uses generated adapters and shared platform shells, forms, grids, saved views, dossiers, projections, and engineering workspaces.

The implementation ledger is [docs/v1-completion-status.json](docs/v1-completion-status.json). It records actual status and remaining work per subsystem. The retained 605-item catalog is a required inventory; generic family rendering/certification is checked by `scripts/catalog.py --check --release`, while domain-specific browser, accessibility and performance maturity remains explicit in the ledger.

## Verification

Run the local gates from the repository root:

```bash
python3 dev contracts
python3 dev architecture
python3 dev lab-build
python3 dev test-lab
python3 dev verify
```

The direct frontend gates are:

```bash
cd frontend
npm ci
npm run typecheck
npm test
npm run build
npm run build:storybook
npm run test:e2e
```

Current machine-readable reports are written under `evidence/current/`. They distinguish passing local checks from external company/macOS qualification and do not issue a production certificate.

## Safety boundaries

Do not use the local profile with company data. Do not treat UI flags as authorization, a local filesystem probe as mounted-storage qualification, synthetic semiconductor views as SEMI compliance, or axe/browser checks alone as WCAG certification. Attachments, imports, webhooks, backups, migrations, and upgrades require the explicit safety checks documented in `docs/`.

## Documentation

[Release status](docs/RELEASE_STATUS.md) · [Completion matrix](docs/v1-completion-status.json) · [Component coverage](docs/COMPONENT_COVERAGE.md) · [Master design](docs/MASTER_DESIGN.md) · [Testing](docs/TESTING.md) · [Company qualification](docs/COMPANY_QUALIFICATION.md) · [Recovery](docs/RECOVERY.md) · [Upgrade process](docs/UPGRADING.md)
