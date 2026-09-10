# Migrations, backup and isolated restore

Read DEPLOYMENT.md before executing operator commands. For qualification
drills, configure `BASE_ENVIRONMENT=qualification`, `BASE_PROFILE=company`,
`BASE_QUALIFICATION_PREREQUISITES_FILE`, the exact disposable root and
deployment ID. For final production maintenance, use the complete
`BASE_QUALIFICATION_FILE`. Local development commands deliberately clear
company settings.

Migration heads are read from the Alembic scripts for registry and tenant branches. Add new migrations to those branches; do not change a kernel constant. Database startup is read-only with respect to schema. Never let an application redeploy silently mutate all tenant schemas.

After stopping the application and **every trusted direct writer**, run:

```bash
./dev operator backup --output /approved/backups/new-snapshot --maintenance APP-STOPPED
./dev operator restore --snapshot /approved/backups/new-snapshot --target /approved/drills/new-root
```

Use the exact created snapshot path. Both destinations must be appropriate operator-approved locations; restore requires a new empty root. The command does not overwrite live data. Inspect manifest hashes, integrity and tenant coverage. To rehearse migrations, configure BASE_DATA_ROOT to the isolated restored root and matching non-live qualification, then run:

```bash
./dev operator migrate --maintenance APP-STOPPED
```

Do not move a production qualification file between data roots: root and deployment binding must match the rehearsal environment. Never supply APP-STOPPED while external writers remain active. The token is not a lock and the tool cannot discover arbitrary external applications.

The backup command performs the qualification or production maintenance checks
required for an offline operation, according to the configured environment. In
qualification it requires the prerequisite record but does not require final
runtime evidence; in production it requires the complete final qualification.
It does not open the upload surface and therefore does not certify an
attachment scanner. Application startup and `preflight` still fail closed for
`scanner_required` without a configured scanner. Object-backed attachments are
included in the snapshot and are verified against the staged tenant database;
a missing or inconsistent referenced object fails the backup.

Rollback procedure: stop writers, preserve diagnostic evidence, select an approved application version and compatible data snapshot, restore to an isolated root, validate integrity/schema and tenant access, explicitly repoint the deployment, and run routed smoke tests before resuming writes. Never replace only the main SQLite file of a live database. Define loss tolerance and recovery time before an actual incident.

Current backup scope includes the registry database, active tenant databases, and every object-backed attachment referenced by those databases. The snapshot manifest is schema version 2 and records database hashes plus each object's tenant, validated object key, snapshot path, size, SHA-256 and content type. A missing or mismatched referenced object fails the snapshot; the live root is never modified. Unreferenced local objects remain in place and are listed as `orphan_objects` rather than silently being treated as canonical backup data.

Restore validates all database and object hashes, tenant coverage, object-key safety, symlink absence and attachment metadata consistency before copying anything into a new staging root. It then atomically publishes that new root and never overwrites a live root or the source snapshot. The current application snapshot contract is for `LocalFilesystemStorage`; a provider that declares externally managed backup must supply separate provider evidence and must not be represented as an application-complete snapshot.
