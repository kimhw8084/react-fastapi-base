# Migrations, backup and isolated restore

Read DEPLOYMENT.md before executing operator commands. BASE_ production configuration and identity are inherited for operator tools. Local development commands deliberately clear company settings.

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

Rollback procedure: stop writers, preserve diagnostic evidence, select an approved application version and compatible data snapshot, restore to an isolated root, validate integrity/schema and tenant access, explicitly repoint the deployment, and run routed smoke tests before resuming writes. Never replace only the main SQLite file of a live database. Define loss tolerance and recovery time before an actual incident.

Current backup scope includes registry/tenant databases and the BLOB attachments they contain. Runtime configuration, environment secrets, code and external files are separate operator-managed assets. Large-file storage adapters will need an explicit backup policy; they are not automatically covered.
