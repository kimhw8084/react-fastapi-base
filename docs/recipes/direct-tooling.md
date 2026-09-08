# Trusted direct database tooling

app/tooling/work_items.py demonstrates an explicit company identity, tenant membership and permission check, then calls the same domain service inside the same transaction and audit path as HTTP. It is app-owned composition, not an import from the platform back into a domain.

Use only on the qualified same-host database topology and with explicit operator-controlled environment. Do not create random sqlite3.connect calls around the repository. Reusing this helper does not prevent another process with filesystem write access from bypassing it. OS access controls and operator discipline are separate requirements. Multiple arbitrary APIs on separate hosts are not supported by this release.
