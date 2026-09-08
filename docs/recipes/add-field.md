# Add a domain field

Inspect work_items/models.py, schemas.py, definition.py and the reference tests. Define storage constraints and API validation first. Add an Alembic tenant migration with a safe default/backfill for existing rows; do not use create_all at startup. Update history snapshots and intentional restore/revert behavior when the field belongs in them. Update CSV format/version policy explicitly rather than silently breaking saved exports.

Expose the field through the feature definition; ordinary text/select/textarea rendering can remain generic. Use a feature custom component for complex editing. Run ./dev contracts, affected backend tests, ./dev architecture, then ./dev verify. Test old database migration, create/update validation, a stale edit, archive behavior, permissions and export/import. Do not add domain knowledge to platform schemas merely to save one feature file edit.
