# Template upgrades

The review build implements a hash-bound, conflict-refusing upgrade apply and rollback for the managed platform core. The disposable fixture at `scripts/upgrade_fixture.py` proves generated-app migration, contract regeneration, frontend tests/build, apply, rollback and integrity restoration. It does not migrate application-owned schema or silently reconcile local divergence.

`./dev create` records managed kernel hashes in template.lock.json. Config, theme, app composition and concrete features are application-owned. A subsequent plan compares original/current/incoming hashes:

```bash
./dev upgrade-plan --app ../my-app --incoming ../react-fastapi-base-next
```

Unchanged local core plus changed incoming core yields an update. A changed local file plus unchanged incoming file preserves local ownership. A two-sided difference yields a conflict. The command does not write any files and returns nonzero for conflicts. It never guesses an AI merge.

Review the plan hash and resolve every conflict before applying. Apply requires the exact plan hash and `--maintenance APP-STOPPED`; it journals atomic file changes and preserves application-owned configuration. Regenerate contracts, run all gates, and keep the journal for rollback. Rollback refuses to overwrite post-upgrade human edits. Application-owned migrations and specialized reference-app generation remain separate domain responsibilities.

Semantic version policy proposed for v1: patch preserves public APIs and behavior; minor adds compatible capability; major changes contracts or requires application adaptations. Database and saved-view schema changes get explicit migrations even when npm/Python package versioning would allow a minor update. A code-file three-way merge is not a data migration.
