# Release status — react-fastapi-base 1.0.0-rc.12

## Decision

**V1 LOCAL CODE COMPLETE — COMPANY QUALIFICATION PENDING.** RC.12 adds the canonical UI state matrix and accessibility regression gate on top of the schema-v2 CompanyQualification contract. All locally achievable V1 contracts in [v1-completion-status.json](v1-completion-status.json) remain source-backed verification; this is not a company production certificate.

RC.10 configuration/secrets and earlier release evidence remain immutable historical evidence for their exact sources. RC.11 does not rewrite or relabel those reports.

RC.12 preserves RC.11 evidence as historical for its exact source and binds the new UIQA matrix/results to the verified RC.12 source. The local browser gate does not prove the final company/profile `ui_accessibility` qualification.

## Current local proof

- Backend: 270 tests passed across the deterministic four-shard runner; generated contracts, migrations, architecture checks, security-source checks and owned statistical/performance checks passed.
- Frontend: locked `npm ci`, TypeScript, 17 Vitest files / 44 tests, production build, Storybook build and 26 Playwright workflows passed, including the 13-row canonical UI state matrix.
- Browser proof covers create/reload/dossier tabs, dirty navigation, team saved views, administration events/teams, every registered workspace, mobile keyboard/axe, a 100k logical-row bounded table, and major surfaces at 200%/400% zoom with reduced motion and high contrast. Tested workflows reported no browser console errors or page errors.
- Platform proof covers server-owned computed fields, generic relationship explorers, saved-view schema reconciliation/conflict recovery, universal dossier compare, deterministic attachment scanning, typed integration adapters, and relationship-set stress.
- `scripts/catalog.py --check --release` passes all 605 retained catalog entries without wrapper-only certification.
- Seven generated reference applications pass their migration, contract, frontend test/build and source-integrity proofs. The upgrade fixture passes plan, conflict-safe apply, migration, build/tests, rollback and integrity comparison.
- Deterministic performance stress passes the table, planning, graph, rack, wafer, observability, dashboard and SPC workloads. The exact-candidate clean-install proof passes without reusing the working tree's virtualenv, node modules or caches; on Linux it is the portable code gate and macOS-specific qualification is recorded as BLOCKED, while the current Darwin evidence also passes macOS qualification.
- RC.2 hardens object-inclusive backup/restore, fails closed when production uploads have no malware scanner, renews long-running job leases, refreshes the deterministic source manifest, clarifies the historical requirements ledger, and makes archived/viewer dossier comments read-only.
- RC.3 centrally enforces the attachment upload policy for every caller, binds object export to the copied snapshot database, rejects archived comment deletion server-side, and reconciles the supported Python runtime documentation.
- RC.4 hardens attachment metadata and download integrity, binds direct service calls to the authenticated tenant, validates qualification attestations, and keeps upload-scanner readiness separate from offline maintenance safety checks.
- RC.5 makes archived-record immutability authoritative in the shared attachment service, closing the direct-service bypass left outside route-level checks.
- RC.6 separates authorized company qualification staging from final production qualification. A strict prerequisite record enables provision, migration and object recovery drills without weakening the final `CompanyQualification` requirement; qualification readiness remains explicitly `production_ready: false`.
- RC.7 is the bounded UI remediation candidate: shared semantic tokens, the v36 AG Grid theme API, native checkbox control geometry and Experience Lab label renderers were corrected against rendered evidence. RC.6 remains immutable historical certification for its exact source and does not qualify this changed executable source.
- RC.8 adds the canonical server-side CompanyProfile/ProfileRuntime composition seam, typed identity/storage/deployment ports, profile-owned local adapter construction, request-aware identity resolution and dependency/public-runtime regression coverage. CHG-6 RC.7 evidence remains immutable historical evidence for its exact source.
- RC.9 adds the API major 1/revision 1 policy, safe bootstrap negotiation, generated frontend metadata, and a Git-native deterministic OpenAPI compatibility gate for the actual review base. It remains independently deployable and does not alter company identity, storage, deployment semantics or production readiness.
- RC.10 adds the single metadata-only configuration/secrets contract, fail-closed reserved namespaces, explicit Settings precedence, pure-before-runtime validation, redacted secret handling and publisher/runtime boundary checks. It does not alter the API major/revision or company qualification contract.
- RC.11 adds the final composite CompanyQualification schema v2, exact eight-gate enumeration, derived readiness, secret-safe durable evidence references, legacy-schema migration refusal, deterministic source-bound readiness matrix and RC.11 evidence-manifest binding. API major 1/revision 1 remains unchanged; company/profile gates remain external and visibly BLOCKED.
- RC.11 R2 repairs source/evidence binding: production requires the repository-owned `deploy/rc11-release-identity.json` and rejects self-consistent operator source identities that do not match it. BUILD evidence records only verified source/evidence/target-base facts; Accepted Head and repository merge SHA remain later workflow facts. API major 1/revision 1 remains unchanged; company/profile gates remain external and visibly BLOCKED_EXTERNAL.

Current machine-readable evidence is under `evidence/current/`, especially [verification.json](../evidence/current/full-stack/verification.json), [backend-junit.xml](../evidence/current/full-stack/backend-junit.xml), [object-restore.json](../evidence/current/recovery/object-restore.json), [browser-e2e-accessibility.log](../evidence/current/full-stack/browser-e2e-accessibility.log), [stress.json](../evidence/current/performance/stress.json), [reference-apps.json](../evidence/current/release/reference-apps.json), and [fresh-clone-macos.json](../evidence/current/full-stack/fresh-clone-macos.json).

## External qualification only

- Real company AccessKey multi-user topology and identity isolation.
- Provider-mounted SQLite locking, journal, durability, redeploy persistence and backup/restore qualification.
- Company frontend/backend publication, ingress, restart and redeploy drill.
- Company-operated backup/restore and recovery drill.
- Applicable company/profile UI accessibility, performance and operations evidence.

Optional authenticated realtime push, enterprise malware/CDR provider selection, independent penetration testing and non-Chromium/manual screen-reader qualification are not misrepresented as local production certification or local release blockers.

## Evidence policy

Reports under `evidence/current/` are generated from the current source and carry commit, timestamp, command, exit code, environment and hashes. Historical reports remain under historical directories and are not release proof. Local success does not certify company infrastructure, SEMI compliance, WCAG conformance, or production safety.

The deterministic RC.12 repository readiness report is `evidence/current/release/rc12-readiness-matrix.json`; its companion manifest and binding are `rc12-manifest.json` and `rc12-evidence-binding.json`. The UI matrix/result evidence is under `evidence/current/uiqa/`; all are repository evidence, not an operator-approved qualification file.
The repository identity is generated from the passing current source verification report by `scripts/generate_release_identity.py` and is intentionally outside the executable-source hash set to avoid a digest cycle. Its `source_commit` is the verified executable-source commit; the later evidence and Fabric branch heads do not replace it.
