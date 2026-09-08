# Permissions and users

The identity source identifies the actor; membership grants a tenant role. Edit server config permission sets only through trusted development/deployment processes. Add checks in each domain service and negative tests before adding visible controls. Test a viewer calling the endpoint directly, an editor invoking admin actions, and another tenant's IDs. Browser conditional rendering is not the security boundary.

Use explicit operator provisioning and add-member for new membership. This review CLI refuses silent overwrite of existing membership. Role revocation/change UI and workflows still need implementation; do not edit the database ad hoc without an audited maintenance process. Adding an entirely new role ID needs a schema migration because the registry constrains roles.
