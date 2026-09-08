# Security and trust boundaries

This is not a security certification or a claim of complete OWASP ASVS/WCAG compliance. The current code is review software with blocked dependency/browser/company gates.

## Protected assets and controls

Company identity is established outside the app, then resolved only through the AccessKey adapter. Every data request checks tenant membership server-side. Roles are configured on the server. CSRF tokens bind user identity to mutations. Production requires explicit HTTPS origins, host allowlists, a sufficiently long operator-supplied random CSRF secret, and a validated qualification file. No demo/admin fallback is allowed in the company identity provider.

Concrete model validation, constrained tenant paths, bounded payloads, explicit query-sort allowlists and transaction revision checks protect the reference write path. Mutable shared API clients are not used across tenant switches. Audit entries are appended in the same transaction as domain writes. API error responses never include SQL or stack traces. Browser runtime JSON is nonsecret.

The native frontend server constrains static paths/hosts, rejects API fallback, applies CSP and no-store runtime config. Equivalent controls are required if a corporate static publisher replaces it. Per-process request limiting is only defense in depth; authenticated ingress and platform-wide limits remain the operator's job.

## Limits that must not be hidden

A user with raw writable database access can bypass application authorization and can alter schema/audit triggers. The direct-tooling service path is a supported convention, not an OS security sandbox. Use separate service identities and real filesystem ACLs. If all per-user app processes inherit the same writable mount, assess whether an untrusted user can execute arbitrary code in that environment. App-level permissions cannot compensate for unrestricted file access.

S3-mounted path support, multi-user identity isolation, backups, network ingress and company secrets are unverified. Malicious documents are not scanned by an antivirus/CDR engine. The in-process rate limiter is not distributed. No full integration/webhook/SSRF stack is implemented. Session revocation depends on the corporate runtime plus registry membership management; no arbitrary multi-user session provider is bundled.

The current Python dependency snapshot is exact but unhashed and only locally exercised. Frontend dependencies are unresolved candidates without a lock. Neither dependency set has a completed advisory scan in this environment. Do not use version numbers alone as evidence of security.

## Acceptance

Run security/authorization/tenant-negative tests and intentional misuse cases, dependency scans, actual browser tests and an independent threat review. Revoke role/tenant access and verify cached UI cannot perform backend actions. Test external callbacks and uploads before enabling new packs. Capture approval against an exact artifact digest.
