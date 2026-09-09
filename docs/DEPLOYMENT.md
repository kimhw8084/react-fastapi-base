# Company PaaS deployment contract — not yet exercised on company infrastructure

## Hard boundary

No provided command publishes or changes a live company deployment. Code readiness, source review, dependency clearance and company qualification are all required. Do not bypass a missing qualification by selecting development mode.

## Backend project

Root: backend/. Native ASGI import: app.main:app. Optional starting file: run.py. Python 3.13 is the measured runtime in this delivery; validate any other corporate runtime.

```bash
python -m pip install -r requirements.lock
python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
```

The file entrypoint runs that same ASGI application. Configure the publisher's own start/import mechanism when it owns Uvicorn. No implicit migration is performed at startup. Supply production env through the PaaS configuration service, not a committed .env. AccessKey must be injected by the platform for the actual caller's isolated execution; do not manually set it to the app owner for a shared service.

Health is /api/v1/health; readiness is /api/v1/readiness. Readiness includes expected migration heads for active tenants and fails on invalid production configuration. A healthy endpoint is not proof of user identity or storage durability.

## Frontend project

Root: frontend/. Clean build, after resolving and reviewing the first lock:

```bash
npm ci
npm run build
```

Static publisher: serve dist/ with SPA navigation fallback, but never rewrite /api into index.html. Set equivalent security headers to frontend/server.mjs. Required runtime config must use the separately published FastAPI HTTPS origin unless the ingress actually provides same-origin API routing.

Node starting-file publisher: server.mjs, with PORT supplied by PaaS. Set NODE_ENV=production, explicit BASE_FRONTEND_HOSTS (JSON array), and optional BASE_FRONTEND_RUNTIME_CONFIG. See the file's native contract. It serves assets only; it does not implement company authentication or reverse proxying. CSP permits inline style geometry for AG Grid but forbids inline scripts/eval. Company embedding requires an explicitly reviewed frame-ancestors policy change.

## Deployment order

1. Resolve and review exact dependencies, run code/browser/security gates, bind evidence to the source digest.
2. Obtain actual AccessKey identity/topology and persistent-store guarantees; complete COMPANY_QUALIFICATION.md.
3. Provision a separate staging root and explicit memberships. Never seed demo data into a company root.
4. Stop all relevant writers; snapshot and isolated restore rehearsal; migrate registry and every tenant intentionally.
5. Publish backend and frontend independently, with matching API-contract versions and HTTPS origins.
6. Use two real company users to exercise role/tenant differences in the actual browser path. Check redirects, cookies, CORS and inaccessible direct backend routes.
7. Test restart, redeploy, rolling overlap policy, persistent data and recovery. Record actual evidence in operator-controlled storage.
8. Require release approval for the precise artifact and environment. Do not describe this review archive as a certified release.

If per-user PaaS replicas run on different hosts against one mounted database, the current conservative SQLite profile is not compatible. Resolve with a supported shared database service or an owner process/API; a journal-mode change or extra retry is not the fix.

## Attachments and production upload policy

The application uses a tenant-scoped object adapter for runtime attachments. Local `LocalFilesystemStorage` objects are included in the application snapshot and restore contract. A provider-managed object store must declare its backup/retention boundary and provide independent qualification evidence; a database-only snapshot is never considered complete for object-backed rows.

Production defaults to `BASE_ATTACHMENT_UPLOAD_MODE=scanner_required`. Startup/readiness fails closed while that policy is selected if the configured scanner is `NoopMalwareScanner`. `trusted_types` and `disabled` are explicit deployment choices; development and test use the deterministic scanner. The malware/CDR provider remains a company deployment adapter, but production must not silently present a no-op as malware protection.

## Durable jobs

Long-running handlers are executed outside the database write transaction and
their lease is renewed no less often than once per third of the configured
lease. Fencing prevents a stale worker from finalizing a reclaimed job. It
does not reverse an external side effect that already happened, so webhook and
other provider-facing handlers must supply provider idempotency, an event or
idempotency key, or a fencing-aware destination.
