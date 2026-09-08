# Customization guide

## Product configuration

Edit backend/app/config/application.json. Its schema lives in platform/configuration.py. Name/description/navigation labels/order are validated and delivered through bootstrap. Restart the backend after edits. Do not put credentials in this file. Edit backend/app/config/permissions.json for role permission sets; membership data is separate. Existing role IDs are constrained by the registry database; a new role needs a reviewed migration, not just a UI label.

## Browser runtime

frontend/public/runtime-config.json has exactly schemaVersion, apiBase, defaultTheme and titleOverride. apiBase is an origin without /api/v1, path, credentials or trailing slash; blank requires an actual same-origin ingress API route. The optional Node server does not implement that proxy and deliberately returns 404 for /api. For separate publishers set an explicit HTTPS backend origin. A static publisher needs the runtime file copied into the published artifact; editing your local source file does not magically change an existing deployment. The Node publisher may use BASE_FRONTEND_RUNTIME_CONFIG to read an operator-managed nonsecret runtime file.

## Theme and shell

Change semantic tokens in frontend/src/theme/tokens.css, not arbitrary product colors in platform code. operations/clarity/minimal are source implementations, not visually certified designs. Custom React shell composition belongs under src/app. Logos, alternative navigation structures and full localization still require source additions; the current configuration is not a no-code builder for every possible design.

## Workspace and domain

Define fields/columns/capabilities in the backend feature definition, backed by concrete Pydantic schemas and a concrete SQLAlchemy domain model. Regenerate contracts. Register a frontend renderer in src/app/registry.tsx. The normal renderer composes TableWorkspace with a feature adapter. A custom renderer can use a different body while sharing transport, identity and UI primitives. No kernel imports the app's business feature.

Use the generated operation map through ApiClient.call when supported. Domain services own transaction-sensitive invariants, not metadata. Every new permission is implemented and tested server-side before controls are exposed. Hidden buttons and disabled navigation are convenience only.

## State and isolation

Client cache keys include user and tenant. Working preference keys include app, user, tenant and a schema version. Store presentation state only, not credentials or sensitive records. Server saved views use typed, bounded schemas and revisions. Shared views currently mean everyone in the tenant, not an LDAP group. A remote 409 requires reconciliation; never silently overwrite another user's change.

## Proof obligations

Changing a theme should not alter any managed-core hash. Adding a feature should primarily edit features/config/composition. If common code must change, document which reusable behavior is missing and add a regression test for existing features. Do not assume three palette variants prove that the entire product is maximally customizable.
