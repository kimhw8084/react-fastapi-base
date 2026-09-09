# Architecture decisions

## ADR-001 — Separate native PaaS roots

Decision: retain backend/ and frontend/ with native entrypoints, optional Node static server and no container dependency. Reason: explicit company deployment requirement. Alternative rejected for v0: mandatory combined Docker image. Consequence: origins/cookies/ingress must be qualified separately. Proof: local static publisher and HTTP backend checks, followed by actual PaaS publication (pending).

## ADR-002 — Env identity is a topology constraint

Decision: AccessKey-only company identity behind one adapter; production requires user-isolated execution. Rejected: browser username fallback, shared-process env mutation per request, invented company auth headers. Consequence: a shared single-username process cannot safely satisfy multi-user requirements. Proof: two real simultaneous company sessions and ingress isolation, pending.

## ADR-003 — Never infer SQLite support from mount visibility

Decision: DELETE/FULL as one conservative database profile on provider-qualified storage; no automatic journal selection or probe-issued certificate. Rejected: WAL everywhere, DELETE as universal S3 workaround. Consequence: the current profile may be incompatible with the company's actual storage/topology. Proof: provider guarantees and company recovery qualification, pending. Local diagnostics merely test observed mechanics.

## ADR-004 — Sync SQLAlchemy for this bounded implementation

Decision: synchronous SQLAlchemy in synchronous FastAPI endpoints and trusted tooling. Reason: short SQLite operations and a single concrete connection/transaction policy; executable with the verified runtime. Rejected for this build: copying SysGrid's async layer solely for fashion. Consequence: limits on long-running database work; background jobs and external async providers need their own design. Proof: backend tests and real localhost HTTP; production load pending.

## ADR-005 — Concrete domains, generic workspace UI

Decision: shared presentation/state contracts, concrete feature models/services. Rejected: one untyped universal entity table or a giant no-code JSON application engine. Consequence: new domain rules still need code/tests, but do not require rewriting modals/grid/transport. Proof: reference work-items plus the seven generated reference-app fixtures pass; specialized domain qualification remains separate.

## ADR-006 — Pydantic/OpenAPI owns the wire contract

Decision: generated TypeScript data/operation definitions, deterministic --check. Rejected: independently hand-maintained front/back workspace schemas. Consequence: the limited in-repo generator needs extension tests for unsupported schema forms. Migration to a qualified standard OpenAPI generator is allowed. Proof: generation drift check and pure typed-client runtime tests; full React typecheck pending.

## ADR-007 — Preserve semantics, not historical repair CSS

Decision: semantic CSS variables and three themes; no copied SysGrid global wildcard overrides or embedded product color strings. Tailwind is not required in this review build. Consequence: visual parity must be measured, not assumed; a company requiring Tailwind can add a tested styling layer. Proof: core hashes unchanged under generated theme variants; real visual proof pending.

## ADR-008 — Small attachments inside SQLite

Decision: bounded BLOBs for transactional attachment metadata/content and simple backup scope. Rejected: pretending an unimplemented object store is available. Consequence: limited document size, database growth and no antivirus/CDR; larger files require an explicit provider pack. Proof: attachment tests and backup restore; enterprise file policy pending.

## ADR-009 — Review-build, not self-certified release

Decision: fail closed and retain a complete scope ledger. Rejected: rename unrun checks PASS, silently narrow scope to CRUD, or label missing corporate proof a minor detail. Consequence: user cannot deploy this archive as a certified v1. Proof: verification and release reports list blocked gates and unfinished capabilities.

## ADR-010 — Vendored source with conservative upgrade planning

Decision: app-owned config/features and hash-managed kernel. Rejected for initial delivery: unexplained package registry dependencies or auto-overwriting downstream apps. Consequence: upgrades need a reviewed patch until atomic apply/codemods are implemented. Proof: generator and three-way conflict tests.

## ADR-011 — Shared views are tenant-wide in v0

Decision: scope values personal/team, where team presently means tenant membership. Rejected: infer corporate directory groups from a username variable. Consequence: UI explicitly says tenant-wide, and true teams remain unimplemented. Proof: saved-view privacy and tenant-isolation tests.

## ADR-012 — Mutation/recovery operations never rewrite audit history

Decision: revision preconditions, atomic bulk, new audit revisions for revert, no hard delete/purge API in the reference domain. Rejected: silent overwrite and destructive restoration to live root. Consequence: purge/retention need a separate explicit policy and implementation. Proof: stale-write, atomic rollback, immutable audit and isolated restore tests.
