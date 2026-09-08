# SysGrid migration plan — not executed

Do not replace working SysGrid with this review build. Its complete domain behavior is not implemented here. Keep existing data paths, routes and deployment untouched while developing the template separately.

First finish dependency/browser gates and perform a pinned, exhaustive source inventory. Capture Monitoring's actual routed behavior and screenshots at known viewport/theme/fixtures. Protect semantic requirements through tests, not simply a “looks like Monitoring” prompt. Inspect recent Project changes independently.

Then select one low-risk table consumer and introduce an adapter behind an explicit developer/staging route switch. Preserve API contracts and data models initially. Move repeated presentation/interaction ownership into the platform one responsibility at a time. Do not simultaneously upgrade every framework, change identity, change database layout and migrate the view.

Acceptance per consumer: all original user journeys, role/tenant denials, deep links, manual column sizing, grouping/selection scope, dirty form behavior, history/revert, import/export and diagnostics are either preserved or have a specifically approved intentional change. Test both API and actual browser. Do not compare merely counts of tests or screenshots.

After two materially different table domains, migrate a relationship-rich or analytical domain. Only after these real consumers work should template abstractions be frozen for v1. The neutral work-items example is useful but not a substitute for this proof. No current artifact performs migrations, rewrites views or deletes legacy SysGrid files automatically.
