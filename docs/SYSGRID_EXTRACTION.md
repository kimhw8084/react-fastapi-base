# SysGrid extraction evidence and limits

Reference commit: `66244b997a70b85e6e887870c96db958f3f0d22d`. **No SysGrid files were changed. This is not an exhaustive file-by-file audit or a completed migration.** The new code is a bounded implementation informed by selected contracts and the user’s stated environment. A tree listing is not equivalent to reading every file. Historical audit reports are historical evidence, not proof every listed bug remains at the pinned commit.

| Source path | Classification | New ownership/intent | Evidence coverage |
|---|---|---|---|
| frontend/src/components/shared/OperationalWorkspace.ts | Behavioral contract reference | Typed workspace definitions; retain domain rules in features. | Pinned source reread during this execution; selected lines, not full-repo audit. |
| frontend/src/components/shared/LayoutPrimitives.tsx | Refactor concept, not direct copy | Semantic theme tokens and reusable shell/command surfaces. | Read in earlier repository inspection; no live visual proof. |
| frontend/src/components/shared/OperationalWorkspaceShells.tsx | Refactor concept | Shared table frame; richer hybrid/analytical bodies pending. | Earlier sampled source inspection. |
| frontend/src/components/shared/OperationalDataGrid.tsx | Refactor and qualify | DataGrid/TableWorkspace; error/empty/loading separation. | Earlier sampled source inspection; interaction parity pending. |
| frontend/src/components/shared/OperationalGridInteractions.ts | Pending extraction | Preserve modifier/range/group selection and context-menu semantics. | Referenced by inspected audits; no claim of full current-file verification. |
| frontend/src/components/shared/CollaborativeWorkspaceViews.ts | Reimplement bounded subset | Revisioned personal/tenant-shared saved views; true team/offline/favorite gaps retained. | Earlier sampled source inspection. |
| frontend/src/components/shared/WorkspaceModal.tsx | Behavioral reference | Native dialog/dirty contract, not a wholesale implementation copy. | Reference through prior callsites; complete equivalence unverified. |
| frontend/src/components/MonitoringGrid.tsx | Reference domain, not kernel | Neutral work-items feature demonstrates reusable patterns; Monitoring business logic stays out. | Earlier sampled source inspection. |
| frontend/src/components/ServicesReal.tsx | Migration candidate | Closest table-domain consumer after reference proof. | Historical audits cited; current complete source not audited. |
| frontend/src/components/External.tsx | Migration candidate | Relationship-rich consumer; do not flatten into basic CRUD. | Historical audits cited; no migration performed. |
| frontend/src/components/AssetReal.tsx | Domain-only plus future extraction | Preserve asset semantics, remove repeated platform ownership gradually. | Earlier tree/source sampling only. |
| frontend/src/components/FAR.tsx | Analytical reference candidate | Keep scoring/investigation semantics domain-owned. | Earlier structural tests read; no current end-to-end audit. |
| frontend/src/App.tsx | Refactor concept | Small app composition and renderer registry. | Earlier sampled source inspection. |
| frontend/src/index.css | Refactor, never copy repair pile | Semantic tokens and scoped styles. | Earlier sampled source inspection. |
| frontend/src/api/apiClient.ts | Refactor concept | Typed transport, bounded diagnostics and immutable tenant scope. | Earlier source read; new transport independently tested. |
| backend/app/api/workspaces.py | Refactor contract ownership | Pydantic workspace source of truth plus generic saved-view service. | Earlier sampled source inspection. |
| backend/app/api/utils.py | Company profile reference | AccessKey-only provider as user specified; trusted-header provider not silently invented. | Earlier source read plus explicit user requirement. |
| backend/app/database.py | Redesign safety profile | Registry/tenant path policy, transactions and provider qualification; no WAL assumption. | Earlier source read. |
| scripts/verify-app.sh | Preserve verification principle | One explicit proof command; disposable data; no skipped checks masquerading as pass. | Earlier source read. |
| DEPLOYMENT.md | Preserve corporate boundaries | Separate native roots, explicit migration and isolated recovery. | Earlier source read; real PaaS unverified. |
| .github/workflows/ai-review-packet.yml | Replace verification ownership | Dedicated frontend working-directory and required lock; CI source included, not run remotely. | Earlier source read. |
| AGENTS.md | Preserve upstream policy | Do not mutate SysGrid or invoke terminal agents under its control-room workflow. | Pinned source reread during this execution. |

No legacy file is authorized for deletion by this table. Resolve live imports, tests and actual feature behavior before retiring any SysGrid code. The pinned commit contains recent Project accessibility changes; these were not ported or certified by this template delivery.
