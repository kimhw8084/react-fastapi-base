# Release status — react-fastapi-base 0.2.0-lab

**DEVELOPMENT RELEASE. NOT PRODUCTION CERTIFIED.**

## Delivered and runnable

The packaged standalone Lab runs from the shipped compiled artifacts with `python3 dev lab`. It contains 23 typed engineering widget families, a configurable light/dark shell, Theme Studio, catalog/usage/limits, command navigation, and deterministic synthetic fixtures. The previous FastAPI/SQLite reference backend, migrations, permissions, audit, records, saved views, CSV/file exchange and operational tools are retained. Source, compiled artifacts and test evidence are preserved together.

Current results are machine-readable in `evidence/current/lab/verification.json` and `evidence/current/full-stack/verification.json`. Every report identifies its source or individual hashes. Older logs under evidence/previous-release and evidence/verification are historical, not proof for the updated source.

## Distinct blockers

1. **Scope:** 605 required inventory entries are retained. There are 23 provisional implemented widget families, not a completed 605-component platform. Full advanced grids, Gantt/CPM, calibrated SPC/statistics, proprietary wafer/protocol formats, all window/form variants, comprehensive industry packs, jobs/realtime/integration providers, full administration and upgrade apply/rollback remain unfinished.
2. **React:** no dependency-resolved frontend lock/install/build. The React widget adapter, `/lab` integration and 23 Storybook stories remain source-level work awaiting real execution. Native widget tests do not substitute for this.
3. **Application integration:** local Lab mutations do not persist to FastAPI. Domain persistence, cross-user revisions, permission/tenant enforcement and real error recovery must be wired and tested per feature.
4. **Security and accessibility:** dependency advisories, supply-chain review, full threat testing, automated axe plus manual assistive-technology assessment, contrast/zoom/browser matrix and performance budgets are not complete. Browser interaction tests alone are not WCAG certification.
5. **macOS:** no actual fresh Mac clean installation was run. The zero-dependency Lab launcher and macOS CI configuration are supplied; operating-system certification remains outstanding.
6. **Company:** AccessKey per-user routing, provider-supported mounted SQLite semantics, worker topology, independent publications, redeploy persistence and restore drill need actual corporate evidence. A successful local storage probe cannot certify an S3 mount. Changing to rollback journaling is not a universal fix.
7. **Reference audit:** SysGrid was sampled as evidence; exhaustive file-level extraction and routed migration parity were not performed. SysGrid remains unmodified.

## Use boundary

Explore and develop using synthetic/disposable data. Do not deploy a company production workload, feed production equipment actions through the examples, or treat local UI permission flags as access control. The company backend profile continues to fail closed without explicit operator qualification.

## Release decision

The native Lab, full React host, backend services, entire scope, target OS and company environment are separate gates. `dev verify` must report nonzero while required code/scope gates are missing. Production status must never be changed by editing a summary boolean or counting generated files.
