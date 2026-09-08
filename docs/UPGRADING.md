# Template upgrades

This review build implements safe **planning**, not automatic application of upgrades.

`./dev create` records managed kernel hashes in template.lock.json. Config, theme, app composition and concrete features are application-owned. A subsequent plan compares original/current/incoming hashes:

```bash
./dev upgrade-plan --app ../my-app --incoming ../react-fastapi-base-next
```

Unchanged local core plus changed incoming core yields an update. A changed local file plus unchanged incoming file preserves local ownership. A two-sided difference yields a conflict. The command does not write any files and returns nonzero for conflicts. It never guesses an AI merge.

Before a real upgrade: back up source and data, review the plan and public API/migration changes, apply a narrowly scoped reviewed patch, regenerate contracts, execute all gates, rehearse database upgrades and document rollback. Safe apply/rollback automation and codemods remain release scope. Do not claim applications automatically inherit template fixes after generation.

Semantic version policy proposed for v1: patch preserves public APIs and behavior; minor adds compatible capability; major changes contracts or requires application adaptations. Database and saved-view schema changes get explicit migrations even when npm/Python package versioning would allow a minor update. A code-file three-way merge is not a data migration.
