# Configuration and secrets contract

This is the repository contract for Project OS CHG-32. The authoritative
machine-readable metadata is
[`deploy/configuration-contract.json`](../deploy/configuration-contract.json).
It contains policy metadata only; it never contains environment values,
credentials, evidence payloads or fingerprints.

## Ownership and visibility

| Surface | Classification | Examples | Browser-visible? |
|---|---|---|---|
| Backend environment | server nonsecret/private | profile, data root, config/policy paths, deployment binding, origins, hosts, limits and upload policy | No |
| Backend secrets | secret | `BASE_CSRF_SECRET`, `BASE_WEBHOOK_SECRET_{SECRET_REF}` | No |
| Operator references | operator evidence/reference | qualification prerequisite and final qualification file paths | No |
| Frontend publisher environment | server nonsecret/private | `BASE_FRONTEND_HOSTS`, `BASE_FRONTEND_RUNTIME_CONFIG` | No; only its parsed safe file can be published |
| Browser runtime JSON | public runtime | `schemaVersion`, `apiBase`, `defaultTheme`, `titleOverride` | Yes, after strict validation |
| Local verification/tooling | development/test-only | Vite, Playwright, Lab and local evidence-output overrides | No |
| Platform exceptions | externally owned | `AccessKey`, `PORT`, `HOST`, `NODE_ENV` | `AccessKey` never; process values are not runtime JSON |

`AccessKey` is a platform/PaaS-owned, process-scoped company identity secret.
Only `CompanyIdentity` reads it. It is not a normal application default or a
browser identity mechanism. Company identity, mounted-storage semantics,
deployment routing and recovery evidence remain external qualification work.

## Precedence and loading

All typed backend values are loaded by `Settings`; no parallel settings
framework or implicit production `.env` loading exists. Precedence is:

1. trusted explicit constructor/tooling override;
2. environment value;
3. declared default policy.

An explicitly referenced config or qualification file is validated by its
consumer at use. It cannot silently override unrelated settings. Unknown or
case-variant backend `BASE_*` keys fail closed. The backend permits the
separate `BASE_FRONTEND_*` namespace when tooling shares an environment; the
Node publisher validates that namespace itself and rejects unknown keys or
invalid shapes.

Development and test retain deterministic local defaults. Qualification and
production require the company profile, absolute persistent root, explicit
deployment binding, HTTPS origins, explicit non-local hosts and a random
`BASE_CSRF_SECRET` of at least 32 characters. Qualification requires the
prerequisite reference; production requires the final qualification reference.
Placeholder examples are documentation only and are never qualification
evidence.

## Validation sequencing

`create_app()` first runs pure environment/profile/format/requiredness
validation, then loads the trusted application and policy files, and only
then constructs the selected CHG-27 `CompanyProfile` and `ProfileRuntime`.
This prevents database, storage, scanner or other dependent runtime resources
from being constructed for invalid pure configuration.

Scanner availability, identity topology evidence, provider SQLite semantics,
deployment routing and final qualification are runtime/deployment checks owned
by the existing profile/deployment adapters and CompanyQualification flow.
Missing external evidence stays `BLOCKED`/unready; local defaults and
diagnostic probes cannot promote it to production readiness. Maintenance
commands retain their separate scanner semantics.

## Secret boundary

`BASE_CSRF_SECRET` and webhook signing values are represented with redacted
`SecretStr` fields. Settings representations/dumps, bootstrap and runtime
responses, error messages, ordinary logs, contracts, checkpoint material and
release evidence contain no secret values. Tests use deterministic sentinel
secrets only to prove absence; real credentials are never needed or copied.

The browser receives only the four strict RuntimeConfig fields above. Publisher
configuration, backend paths, identity, secrets and qualification references
are rejected as runtime properties and are not bundled or served.

Run `./dev contracts` to regenerate/check API artifacts and validate this
configuration contract. Run `./dev architecture` and `./dev verify` for the
repository gates. These local checks do not certify company identity, storage,
deployment or production readiness.
