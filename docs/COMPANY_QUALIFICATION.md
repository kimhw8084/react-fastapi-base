# Company identity and persistence qualification

Status: no real company environment was available in the originating execution. Every production approval is pending.

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

## Evidence file

Copy deploy/company-qualification.template.json to an operator-managed, nonpublic location and replace invalid placeholders with actual approved evidence references. Its schema intentionally refuses the template defaults. Pin deployment_id and persistent_root to the actual environment. An evidence string is an attestation, not cryptographic or independent certification. Only authorized release operators may approve it. A later environment/topology change invalidates the approval.

The app's preflight checks configuration and evidence shape. It does not substitute for build/test/security scans, a complete platform scope, or a company release authorization.
