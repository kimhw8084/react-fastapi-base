# CHG-235 R5 verification evidence

This carrier publishes independently readable evidence for exact R4 candidate `372ba8c0ca5ddbc5eff87fc403e6fc181678e5ea` (tree `8ad5d1a21eccf03f1e623888bf9d4dd789946300`) on exact base `main@67ec2ce5ec44d38ee44d22602035c2554a08e00d`. R5 fast-forwarded the fresh verification branch to that candidate and made no Product/tooling executable-source changes. The canonical 675-file source set equals executable source `b7a8d94bd3daa56e167860dc15ddb63be4833270`, tree `a3e87ee94365672304d468469e8415e4f0d24c80`, digest `e4ff89c0c8041217b4a22ae07ef55a2a0a4ef6c44dc0ca334dbad620e669417c`.

## Browser evidence

The focused R4 theme-readiness spec was rerun from a temporary detached checkout of the exact candidate: 8 passed. Six fresh Chromium contexts (three explicit light, three explicit dark) exercised direct `/system`, client navigation to `/system`, and reload. Each context JSON records computed html/body/heading/semantic-token state before and after axe plus serious/critical and other violation IDs. The negative control induces white text on a light `#f4f6f9` canvas and axe detects the expected serious 1.08:1 contrast failure.

The complete R4 local macOS browser/accessibility suite is retained as prior evidence: 70 passed. The summary lists all 70 names and all 21 high-contrast/reduced-motion/zoom route assertions. The full suite was not rerun in R5.

## Gate and release evidence

R5 reran contracts, architecture, exact-base API compatibility, checkpoint validation and the 99-test work-qualification suite; focused browser readiness also passed. R4's full `./dev verify` and exact-base `./dev verify-release` records are reused and included; the exact R4 release-status document and release-finalization regression log are included. RC.24 release identity/readiness/manifest/evidence binding are exact readable copies; binding status is PASS_SOURCE_BOUND_NOT_CERTIFIED for source digest `e4ff89…` and target base above. API remains major 1, contract revision 2.

## Limits and blockers

- Ubuntu CI for R4/R5: **NOT RUN**; local macOS results do not establish Linux behavior.
- Company qualification, authentic identity/provider storage/deployment evidence and operator qualification: **EXTERNAL / BLOCKED**.
- `production_ready=false`; release status `NOT_CERTIFIED`; no CompanyQualification approval was granted.
- Root cause remains medium-confidence browser test readiness/paint timing. The exact transient frame in original CI was not proved.
- Historical requirements ledger `docs/requirements-status.json` has no CHG-235 item; its authoritative V1 status is `docs/v1-completion-status.json`.
- Original AR-80 Notion ZIP remains unavailable for byte readback. The files in this carrier are individually readable and their sizes/hashes are listed in `manifest.json`.

Stop here for independent Project OS audit. This carrier is an evidence ref, not a merge, deployment or product-source change.
