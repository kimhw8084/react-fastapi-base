# Work-environment qualification

Run `./dev work-qualify` from the repository checkout for the source and candidate you intend to qualify. This is private operator tooling for a real company qualification environment; it does not change product behavior or production policy.

On first run, choose an absolute private evidence directory outside the checkout. The harness remembers that directory in the current operator's private config so `--resume`, `--status`, and `--handoff` can find the same run. Set `BASE_WORK_QUALIFICATION_EVIDENCE_ROOT` to override it. Keep this directory on persistent private storage and never commit it.

```bash
./dev work-qualify
./dev work-qualify --resume
./dev work-qualify --status
./dev work-qualify --handoff
./dev work-qualify --plan
```

`--plan` is read-only. A plain run starts a new stable run ID. `--resume` reruns idempotent local discovery and continues that run; restart/redeploy observations append to the event log. `--status` prints a compact local summary. `--handoff` prints only the deterministic one-line `RFBWQ1` handoff (maximum 300 characters).

## What the harness discovers

It checks the exact repository/project, base commit/tree, branch, full HEAD, executable source commit/digest, current-version repository release identity, changed paths and path hashes, API major/revision compatibility, safe configuration facts, local preflight/readiness, current repository browser/accessibility evidence, and source-bound repository performance evidence. It reads only allowlisted configuration facts; secrets, private roots, hostnames and origins are never included in generated reports. It does not alter environment variables or security policy.

Optional real-deployment probes run only when both `BASE_WORK_QUALIFICATION_FRONTEND_ORIGIN` and `BASE_WORK_QUALIFICATION_BACKEND_ORIGIN` are explicitly set for this qualification. The harness requests runtime config, health, readiness, identity-proof refusal, and docs/OpenAPI **status only**. It never follows redirects, prints response bodies, sends an authorization header, or stores a URL. `BASE_WORK_QUALIFICATION_SCRATCH_PARENT` opts into the existing `doctor-storage --scratch-parent` check; it must name approved disposable scratch, never the configured data root.

## Facts that need an operator

The first report prints the private `runs/<run-id>/incoming` folder and creates source-bound templates. Fill only observations that the repository cannot establish from the checked-out source or safe read-only probes. Keep the generated source/deployment binding fields unchanged. The harness rejects stale bindings, unknown shapes, placeholder provider references and malformed evidence; it keeps unknown values out of reports and records `ATTENTION_UNKNOWN` with sanitized metadata.

- Paste `evidence/browser-probe.js` into DevTools on the deployed frontend while signed in as the selected real user. Save the downloads as `incoming/identity-probes/identity-A1.json`, `identity-B1.json`, `identity-A2.json`, and `identity-B2.json`; perform the provider restart/redeploy; then capture `identity-A3.json` and `identity-B3.json`. The probe emits hashes and allowlisted fields only. It never saves `csrf_token`, cookies, headers, user IDs, tenant IDs or tenant names.
- Complete `incoming/identity-topology.json` only from reviewed provider evidence proving isolated per-user process execution, simultaneous users, and refusal of cross-user routing. Let the harness compute the source document digest without copying it: `./dev work-qualify --reference identity /absolute/path/to/provider-document`, then resume. The path and document contents are never recorded.
- After identity/topology passes, reuse or create a dedicated non-demo tenant. `evidence/tenant-membership.md` gives the existing `provision`, `add-member`, and maintenance-only `migrate --maintenance APP-STOPPED` command forms. Run them only through the intended qualification deployment's operator context. Verify both roles and permissions again through the browser probe. Record only non-identifying outcomes in `incoming/tenant.json` and add the source with `./dev work-qualify --reference tenant_membership /absolute/path/to/operator-record`.
- Complete `storage.json`, `deployment.json`, `ui.json`, and `performance.json` from real company observations. For each source document, run `./dev work-qualify --reference <phase> /absolute/path/to/document` (`storage`, `deployment`, `ui_accessibility`, or `performance`); the harness records only a computed SHA-256. Leave source documents and screenshots in the existing authorized private system. Never include secret-bearing screenshots, raw logs, request bodies, cookies, authorization material, or query strings.
- Complete `incoming/company-operations-evidence.json` using the existing typed `CompanyOperationsEvidence` model. `evidence/operations-drills.md` gives preparation, expected result, and whether the harness or provider/operator performs the action for all seven required drills. Provider-specific controls stay with the provider; the harness does not invent commands or inject outages.

The storage gate requires the typed qualification prerequisite record, real provider SQLite support documentation, same-host client guarantee for the current SQLite profile, exact persistent-root binding, disposable doctor result, restart/redeploy persistence and restore into a new empty root. The original root is never overwritten. Attachment-enabled recovery compares the original and restored attachment-byte SHA-256.

The UI gate combines source-bound repository browser/axe/UIQA results with real deployed workflows, role states, keyboard/focus, semantic accessibility, themes, reduced motion, zoom/reflow at 320px and 390px, and human native assistive-technology evidence. It does not claim WCAG certification. Performance combines source-bound repository regressions with bounded, read-only company-route observations and large-data/AG Grid coverage.

## Outputs and decisions

Each run is private and versioned. It contains `state.json`, append-only hash-linked `events.jsonl`, `report.json`, `report.md`, `next.txt`, `handoff.txt`, `inventory.json`, and safe probe/guidance artifacts. The inventory records SHA-256 hashes and a deterministic bundle digest. Detailed run evidence stays local; there is no GitHub write, Notion/ChatGPT integration, upload, or evidence transport.

Statuses are `PASS`, `FAIL`, `BLOCKED`, `ATTENTION`, and `NOT_RUN`. Every non-pass phase includes stable reason codes, a human explanation, and a deterministic next action. The compact handoff binds candidate version/source digest, a safe deployment hash when available, non-pass gate codes, customization class, short run ID, and digest prefix. It contains no names, paths, private origins/URLs, hostnames, or secrets.

The final report maps evidence to the existing eight CompanyQualification gates. Missing or stale evidence stays blocked. The harness can report `READY_FOR_OPERATOR_APPROVAL` only after every gate is proven; it never writes `approved_by`, `approved_at`, or `production_ready: true`, and never changes `BASE_ENVIRONMENT` to production. The handoff is not an approval or production certificate.

No browser/native assistive-technology, provider topology, company storage, ingress, rollback, performance, or operations fact is inferred from local repository tests. If provider evidence is unavailable, preserve the blocker and resume after an authorized operator supplies the fact.
