# Company identity and persistence qualification

Status: no real company environment was available in the originating execution. Every production approval is pending.

## Qualification bootstrap

The deployment has four explicit environment states: `development`, `test`,
`qualification` and `production`. Qualification is an authorized, disposable,
production-like company-staging phase for gathering final evidence. It is not
production-ready and never substitutes for the final `CompanyQualification`.

Before the staging drills, an authorized operator creates a private
`BASE_QUALIFICATION_PREREQUISITES_FILE` containing only facts knowable before
the drills: the exact deployment ID, `per_user_process` identity topology,
supported storage kind and provider SQLite reference, the assertion that all
database clients share one host, the absolute persistent root, and the
operator authorization/timestamp. The prerequisite schema rejects
placeholders, relative roots, shared-process identity, unsupported storage
kinds and extra final-evidence fields. It must match `BASE_DATA_ROOT` and
`BASE_DEPLOYMENT_ID` exactly.

Qualification startup and operator commands still require the company profile,
real process-provided `AccessKey`, HTTPS origins, explicit hosts, a strong
CSRF secret and the prerequisite file. They do not require the final runtime
drill evidence. Readiness reports `production_ready: false`. Development
identity, demo seeding, implicit migration and automatic database creation
remain unavailable in qualification mode.

After the drills, the operator creates the separate final
`BASE_QUALIFICATION_FILE` with schema-v2 composite gates, actual safe evidence
references, exact candidate/source/version/digest bindings and approval. A
prerequisite file cannot be renamed into a final qualification: production
startup/preflight still validates the complete `CompanyQualification`, exact
project/profile/source/version/deployment/root/storage binding and the selected scanner policy.

## Identity

AccessKey is trusted only because the authenticated platform supplies it. A normal process environment is shared by all requests in that process. With the current provider, production requires per-user process/execution isolation and routing that cannot send Alice to Bob's instance. Do not expose another identity header as a silent fallback.

Using two real sessions simultaneously, record bootstrap user_id, tenant permissions, and /api/v1/identity-proof instance_id/deployment_id. Repeat with interleaving requests and after restart. Verify that authenticated ingress is mandatory and that a user cannot route directly into another user's process. A correct username shown once proves very little. Keep proof metadata sanitized; never record cookies or secret environment values.

## Storage

Identify the actual product and mount type with the company operator. “S3 behind a mounted folder” is not a semantics specification. Obtain documented support for SQLite random writes, locking, atomic filesystem operations and durability for the proposed topology. In this review profile all SQLite clients must be on the same qualified host; unknown multi-host mounts are rejected.

Run the diagnostic only in a disposable scratch directory:

```bash
./dev operator doctor-storage --scratch-parent /approved/disposable/scratch
```

It exercises local mechanics and reports diagnostic_pass. It always leaves production approval false. Successful create/rename/fsync/lock/process-crash tests do not establish distributed failure semantics, cache coherence, power-loss guarantees or provider support. A local test result cannot certify S3FS/AWS Mountpoint. DELETE journal does not make an unsupported filesystem safe.

## Persistence and recovery

Test clean stop/start, republish, host replacement, application-version rollback and power/kill behavior in approved disposable environments. Establish whether temporary disks, object caches or network mounts are involved. Stop all writers for multi-file snapshots. Restore into a new root and rehearse migrations. Set real retention, encryption and access policies for backups.

## Final composite evidence file

The final `CompanyQualification` uses schema version 2. It is a composite
contract with exactly these gates, in addition to the typed infrastructure
bindings: `technical_release`, `identity`, `storage`, `deployment`,
`ui_accessibility`, `performance`, `operations` and `release_evidence`.
Statuses are exactly `PASS`, `BLOCKED` or `FAIL`; `NOT_APPLICABLE` is not a
production status. Every PASS gate needs durable evidence metadata and typed
facts. The `production_ready` value is derived by code and is forbidden in the
qualification file.

The shipped template is intentionally complete but unproven: every gate is
`BLOCKED`, bindings and approval are null, and it cannot certify production.
Schema-v1 records are parsed only to return a migration diagnostic and never
certify schema v2.

## Evidence file

Copy deploy/company-qualification.template.json to an operator-managed, nonpublic location only after the qualification drills and replace invalid placeholders with actual approved evidence references. Its schema intentionally refuses the template defaults. Pin deployment_id and persistent_root to the actual environment. An evidence string is an attestation, not cryptographic or independent certification. Only authorized release operators may approve it. A later environment/topology change invalidates the approval.

The app's preflight checks configuration, exact project/profile/version/source/digest/deployment/root binding and evidence shape. It does not substitute for build/test/security scans, a complete platform scope, or a company release authorization. Local/Fabric verification publishes `evidence/current/release/rc11-readiness-matrix.json`, which is repository evidence and remains `NOT_CERTIFIED`; it does not become an operator qualification file.

Before qualification, verify the deployment uses an explicit attachment upload policy. The default `scanner_required` mode must have a real scanner/CDR adapter; otherwise startup/readiness is rejected. The local deterministic scanner proves only the adapter contract and rejects EICAR/SVG test content. During the company recovery drill, upload an object-backed attachment, stop all writers, run the schema-versioned object-inclusive backup, restore into a second root, and verify the original bytes and SHA-256 after download.
