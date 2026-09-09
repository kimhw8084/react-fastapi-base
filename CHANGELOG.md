# Changelog

## 1.0.0-rc.2 — release-safety hardening

- Added schema-versioned object-inclusive backup and isolated restore for local object-backed attachments, including hash, size, path, tenant coverage and metadata consistency checks.
- Added fail-closed production attachment scanning policy, deterministic local scanner coverage, and cleanup of rejected or failed uploads.
- Added automatic durable job lease renewal during long handlers with fence-loss protection.
- Replaced the stale root checkpoint with a deterministic current-source manifest and release-gate check.
- Clarified the historical requirements ledger and made viewer/archived Dossier comments read-only in both UI and API policy.
- Promoted the release candidate to `1.0.0-rc.2`; company qualification remains external.

## 1.0.0-rc.1 — reproducible React/FastAPI review build

- Added the committed frontend lockfile and reproducible `npm ci` workflow.
- Verified React typecheck, unit tests, production build, Storybook build and actual React browser workflows.
- Added security-driven Python dependency updates and a passing Python advisory scan.
- Fixed generated rich-field enum typing, storage validation, overlay dialog labeling, grid pinning and strict TypeScript issues.
- Centralized release metadata in `VERSION`, wired backend health/bootstrap/Lab/upgrade metadata to it, and added version consistency verification.
- Added the current v1 completion matrix, generic catalog-family registry/certification, isolated clean-clone Mac verification, and refreshed release documentation.

The local V1 code is complete; company identity, provider-mounted storage, deployment and recovery qualification remain external. The seven reference-app proof, upgrade fixture, isolated clean-clone Mac certification and current local code gates are passing evidence.

## 1.0.0-rc.1 — local V1 completion continuation

- Closed the local V1 completion matrix: entity computed-field persistence, generic relationship exploration, saved-view reconciliation, platform shells, universal dossier/action/form contracts, operational table proof, engineering packs, generators, storage/integration boundaries and platform services are now source-backed implementation entries rather than stale partial labels.
- Added persisted high-contrast mode and platform scroll-surface keyboard focus semantics.
- Added a 12-workflow browser gate covering all registered workspaces, major-surface axe checks, mobile keyboard behavior, 100k logical-row bounded rendering, reduced motion, high contrast and 200%/400% zoom.
- Refreshed release evidence to 209 backend tests and distinguished isolated clean-clone macOS execution from company qualification.

Local V1 code is complete. Company identity, provider-mounted storage and company deployment/recovery qualification remain external.

## 0.7.0-rich-field-engine

- Added end-to-end rich field semantics: Markdown, code, JSON object, multiselect, percent, duration, scientific and unit-aware numeric fields.
- Generator now emits SQLAlchemy JSON storage, Pydantic structured validation, units, form controls, draft parsing and readable dossier rendering.
- Added generator protection for SQLAlchemy declarative reserved field names.
- Verified a generated rich entity in an isolated full repository through migration, contracts and FastAPI create/list/update validation.
- Current checkpoint verification: 119 backend tests, 29 tooling tests and 18 pure-client tests pass; architecture/contracts are clean.

## 0.2.0-lab

- Canonical product naming: react-fastapi-base; company profile remains first.
- Persisted typed/compiled Experience Lab with 23 interactive engineering widget families.
- Added light/dark/system themes, density, radius, high-contrast/reduced-motion controls, viewport preview and command navigation.
- Added configurable scheduling/rack presentation, runtime model validation, keyboard alternatives, dirty dialogs and model tests.
- Added carrier/traveler/floor-plan widgets and software workflow examples.
- Added controlled React adapter and 23 Storybook stories; current Storybook and React browser gates execute from the committed lockfile.
- Preserved reference backend, generated API contracts and operator tools.
- Added native static-server tests, strict artifact parity, browser evidence, catalog and atomic checkpoint packaging.
- Fixed calendar portability, wizard drafts, modal keyboard focus, invalid trace summary, wafer coordinate labels and same-origin Lab embedding policy.
- Retained 605 scope items; production and full React/Mac/company certification remain open.

## 0.1.0-review

Original Company Golden review archive, now retained as source provenance. Not production certified.

## 0.11.0 analytics-semiconductor
- Added deterministic SPC/statistics primitives in Python and TypeScript (I-MR, Xbar-R, Cp/Cpk/Pp/Ppk, EWMA, Pareto, run-rule signals).
- Added canonical Process Measurements with a dense SPC projection and Equipment relationships.
- Added semiconductor capability pack entities: Wafer Runs, Manufacturing Lots, Equipment States, Process Recipes.
- Added server-owned wafer yield/bin validation, lot route validation, equipment-state duration, recipe comparison, and typed cross-entity relationships.
- Added Wafer, Lot Traveler, Equipment State/Utilization, and Recipe Compare reusable projections.
- Normalizer ValueError is now converted centrally to a safe 422 domain-validation response.

## 0.12.0 software-engineering-pack
- Added canonical Software Services, Delivery Runs, Observability Events, Incidents and Service Objectives.
- Added typed service/deployment/observability/incident/SLO relationships and service dependency topology contracts.
- Added server-owned pipeline/incident duration, timeline/stage validation, observability validation, and SLO burn/error-budget/status calculations.
- Added reusable Delivery Pipeline, Observability/Trace Waterfall, Incident Command and SLO/Error Budget projections.
