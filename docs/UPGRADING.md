# Template upgrades — 1.0.0-rc.22

The review build implements a hash-bound, conflict-refusing upgrade apply and rollback for the managed platform core. The disposable fixture at `scripts/upgrade_fixture.py` proves generated-app migration, contract regeneration, frontend tests/build, apply, rollback and integrity restoration. It does not migrate application-owned schema or silently reconcile local divergence.

`python3 dev create` records the current platform version, canonical executable-source commit/digest and managed-core hashes in `template.lock.json`. Config, theme, app composition and concrete features are application-owned. A subsequent plan compares original/current/incoming hashes:

```bash
python3 dev upgrade-plan --app ../my-app --incoming ../react-fastapi-base-next
```

Unchanged local core plus changed incoming core yields an update. A changed local file plus unchanged incoming file preserves local ownership. A two-sided difference yields a conflict. The command does not write any files and returns nonzero for conflicts. It never guesses an AI merge.

Review the plan hash and resolve every conflict before applying. Apply requires the exact plan hash and `--maintenance APP-STOPPED`; it journals atomic file changes and preserves application-owned configuration and data. Use the matching commands:

```bash
python3 dev upgrade-apply --app ../my-app --incoming ../react-fastapi-base-next --plan-hash <exact-plan-hash> --maintenance APP-STOPPED
python3 dev upgrade-rollback --app ../my-app --journal ../my-app/.template-upgrades/<journal>/journal.json --maintenance APP-STOPPED
python3 dev upgrade-fixture
```

Rollback refuses to overwrite post-upgrade human edits. The fixture proves a representative application-owned project record survives apply and rollback; it does not claim arbitrary application-owned schema migration. Regenerate contracts, run all gates, and keep the journal for rollback. Application-owned migrations and specialized reference-app generation remain separate domain responsibilities.

Semantic version policy proposed for v1: patch preserves public APIs and behavior; minor adds compatible capability; major changes contracts or requires application adaptations. Database and saved-view schema changes get explicit migrations even when npm/Python package versioning would allow a minor update. A code-file three-way merge is not a data migration.
