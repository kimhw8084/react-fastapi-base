# Company PaaS deployment contract — not yet exercised on company infrastructure

## Hard boundary

No provided command publishes or changes a live company deployment. Code readiness, source review, dependency clearance and company qualification are all required. Do not bypass a missing qualification by selecting development mode.

The backend has separate `development`, `test`, `qualification` and
`production` environments. `qualification` is an authorized, disposable
company-staging phase for gathering final evidence; it is production-like but
always reports `production_ready: false`. It uses the company identity adapter
and real `AccessKey`, never `DevelopmentIdentity`.

## Backend project

Root: backend/. Native ASGI import: app.main:app. Optional starting file: run.py. Backend contract: Python `>=3.11,<3.15`. The current RC.7 release verification environment is recorded in generated evidence; the company PaaS runtime must fall within the supported range and be exercised during qualification.

```bash
python -m pip install -r requirements.lock
python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
```

The file entrypoint runs that same ASGI application. Configure the publisher's own start/import mechanism when it owns Uvicorn. No implicit migration is performed at startup. Supply production env through the PaaS configuration service, not a committed .env. AccessKey must be injected by the platform for the actual caller's isolated execution; do not manually set it to the app owner for a shared service.

Health is /api/v1/health; readiness is /api/v1/readiness. Readiness includes expected migration heads for active tenants and fails on invalid production configuration. A healthy endpoint is not proof of user identity or storage durability.

Attachment policy is part of application readiness: ASGI startup and `preflight` fail closed when `scanner_required` has no real scanner. The offline `migrate`, `backup` and `run-jobs` operator commands do not accept uploads, so they validate the production qualification contract while explicitly omitting scanner availability; their success must never be treated as application readiness. Select `trusted_types` only when the deployment intentionally accepts the bounded MIME/signature/size policy without malware scanning, or select `disabled` to prohibit uploads.

Qualification operator commands (`provision`, `add-member`, `migrate`,
`backup`, `restore` and `doctor-storage`) accept the prerequisite contract so
the drills can generate final evidence. `backup` still requires the literal
`--maintenance APP-STOPPED`; `restore` still requires a new target root. These
commands do not issue a production certificate. Production commands continue
to require the final `CompanyQualification`.

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
2. Obtain actual AccessKey identity/topology and provider SQLite guarantees.
3. Create the private prerequisite record and configure `BASE_ENVIRONMENT=qualification`, `BASE_PROFILE=company`, `BASE_QUALIFICATION_PREREQUISITES_FILE`, the exact root/deployment, HTTPS origins, explicit hosts and strong CSRF secret.
4. Publish the qualification backend/frontend independently, then provision and explicitly migrate the disposable staging root. Never seed demo data into a company root.
5. Use two real company users to exercise role/tenant differences, ingress and routing in the actual browser path.
6. Test restart, redeploy, rolling overlap policy, persistent data and recovery. Stop all relevant writers before snapshot/restore and record actual evidence in operator-controlled storage.
7. Create the final `CompanyQualification` with those evidence references and authorized approval; switch the exact candidate/root/deployment to `BASE_ENVIRONMENT=production` and `BASE_QUALIFICATION_FILE`.
8. Run production preflight/readiness and final two-user smoke, then require release approval for the precise artifact and environment. Do not describe this review archive as a certified release.

If per-user PaaS replicas run on different hosts against one mounted database, the current conservative SQLite profile is not compatible. Resolve with a supported shared database service or an owner process/API; a journal-mode change or extra retry is not the fix.

## Attachments and production upload policy

The application uses a tenant-scoped object adapter for runtime attachments. Local `LocalFilesystemStorage` objects are included in the application snapshot and restore contract. A provider-managed object store must declare its backup/retention boundary and provide independent qualification evidence; a database-only snapshot is never considered complete for object-backed rows.

Production defaults to `BASE_ATTACHMENT_UPLOAD_MODE=scanner_required`. The shared attachment service enforces this policy for every upload caller. Startup/readiness and the service fail closed while that policy is selected if the configured scanner is missing or is `NoopMalwareScanner`. `trusted_types` is an explicit bounded MIME/signature/size policy only and provides no malware scanning; `disabled` rejects every upload. Development and test use the deterministic scanner. The malware/CDR provider remains a company deployment adapter, but production must not silently present a no-op as malware protection.

## Durable jobs

Long-running handlers are executed outside the database write transaction and
their lease is renewed no less often than once per third of the configured
lease. Fencing prevents a stale worker from finalizing a reclaimed job. It
does not reverse an external side effect that already happened, so webhook and
other provider-facing handlers must supply provider idempotency, an event or
idempotency key, or a fencing-aware destination.
