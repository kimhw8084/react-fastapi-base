# Database migration

Choose registry versus tenant ownership. Add a new revision under the matching migration branch; expected heads are discovered from Alembic rather than a core constant. Use explicit constraints/indexes and a safe data backfill. Preserve existing row IDs and revisions. Test both a fresh database and a realistic previous revision.

Stop all application/direct writers, snapshot, restore to a new root and rehearse the migration before touching live data. Only operator-authorized commands may change production schema. Never enable auto-migrate as a workaround for a failing readiness check. A failed migration stays failed and must not be hidden by broad exception handling or test weakening.
