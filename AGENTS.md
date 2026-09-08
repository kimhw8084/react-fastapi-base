# react-fastapi-base repository instructions

This is a separate review-build template. Do not edit, commit or deploy the upstream SysGrid repository as an incidental action.

## First read

README.md, docs/RELEASE_STATUS.md, docs/MASTER_DESIGN.md and the affected feature recipe. Consult docs/requirements-status.json to distinguish implemented, partial and blocked work. Production readiness is not implied by file presence or a green local test.

## Ownership

Normal work: backend/app/config, backend/app/features, frontend/src/app, frontend/src/features, frontend/src/theme. Kernel: backend/app/platform and frontend/src/platform. App composition may import both; core must not import features. Company AccessKey is read only in its identity adapter. No UI identity headers, admin fallback or authorization in frontend flags. Do not add unsafe filesystem assumptions.

## Contracts and tests

After schema changes run ./dev contracts. Run ./dev architecture and ./dev verify. Missing dependencies are BLOCKED, not PASS. Never report a typecheck, browser test, security scan or deployment successful unless actually executed successfully. Generated files are regenerated, not hand-maintained. Keep failing tests meaningful; do not weaken assertions, retries or limits to hide a defect.

## Safety

No implicit database initialization/reset on application start. Never use company/live databases in tests. No production deployment, live migration, identity provisioning, destructive command, external credential handling, commit or push without explicit scope authorization. Backup/migration APP-STOPPED is an operator acknowledgement, not a lock. Do not infer mount safety from diagnostics.

## Completion

Report changed paths, actual commands/results, remaining failures and release impact. One focused unsuccessful repair should result in a diagnostic handoff rather than an unbounded speculative loop. Keep source changes bounded; finish with observed evidence, not self-awarded certification.

## Experience Lab

Source: experience-lab/src. Compiled artifacts: experience-lab/public/lib. Rebuild with ./dev lab-build and verify with ./dev test-lab. React integration is frontend/src/platform/engineering/EngineeringWidget.tsx. A passing native widget test is not a React build, macOS test, WCAG certification, or PaaS qualification. Read docs/EXPERIENCE_LAB.md and catalog/roadmap.json. Preserve the expanded scope; do not label incomplete capabilities Stable. Checkpoint source using python scripts/checkpoint.py after meaningful changes, then validate each archive before delivery.
