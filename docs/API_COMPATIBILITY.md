# API compatibility and versioning

## Canonical contract

FastAPI/Pydantic executable behavior is the wire-schema authority. `scripts/generate_contracts.py` regenerates the committed `contracts/openapi.json` and `frontend/src/generated/schema.ts`; generated drift is a hard failure. The single repository-owned API metadata source is `backend/app/platform/version.py`:

- API major: `1`
- v1 contract revision: `1` for this release’s inaugural explicit revision policy
- public family: `/api/v1/`

API major/revision are independent of application semver. The backend publishes only `api_major` and `api_revision` in bootstrap, plus the same safe values as OpenAPI metadata. No company profile, credential, AccessKey, storage path or qualification evidence crosses that boundary.

## v1 policy

Within v1, additive changes are allowed when existing meanings and values remain valid: new operations and new optional request/response object properties are the primary supported cases. A future externally observable contract change increments the monotonic revision.

The following are breaking: removing or renaming an operation, path, parameter or field; changing method/path semantics; adding a required request field; changing an existing field’s type or nullability; narrowing accepted inputs; changing or removing response variants; and changing existing enum/literal behavior visible to clients. The automated gate also fails closed for behavior it cannot decisively classify.

Breaking changes require a deliberate new major, normally `/api/v2/`, with an explicit migration and overlap plan. Do not silently repurpose `/api/v1/`, and do not use application semver to waive API-major compatibility.

## Independent rollout

Frontend and backend publishes are not assumed atomic. Publish a backward-compatible backend first, keep it at or above the frontend’s compiled required revision during the overlap window, and publish the frontend afterward. The frontend validates bootstrap before workspace definitions or feature data flow. Missing metadata, a major mismatch or an older backend produces a clear bootstrap error and no partial application state. A newer backend revision in the same major is accepted because v1 must remain backward compatible.

## Repository gate

The repository-native gate is `scripts/check_api_compatibility.py`. It resolves the target contract from Git (`git show <base-sha>:contracts/openapi.json`) and never fabricates a copied baseline. The pull-request workflow fetches full history and passes `github.event.pull_request.base.sha`; push verification uses the previous commit when available. A missing or unresolved baseline is `BLOCKED`, never `PASS`. The report is machine-readable and records the resolved base SHA, revisions, classifications and contract hash.

Examples:

```bash
python3 scripts/check_api_compatibility.py \
  --base-ref 86be626e7b6962ffeb3370c80d66c7c0d6ea7a9f \
  --output evidence/current/release/CHG-31-api-compatibility.json
```

`./dev contracts` still checks current generated artifacts, and `./dev verify` runs both generated-artifact drift and the Git-base compatibility gate. The exact base used for review must be explicit in release evidence.
