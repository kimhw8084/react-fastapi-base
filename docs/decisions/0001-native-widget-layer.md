# ADR: reusable native widget layer with a React adapter

Status: implemented provisionally in 0.2.0-lab; React hosting still unverified.

The execution environment could not resolve npm packages. Rather than fabricate dependency locks or label source-only React a passing application, the engineering widget layer was implemented using strict TypeScript, standards-based custom elements and DOM/SVG. The exact compiled modules run in a zero-network standalone Lab and are hosted through a controlled React adapter.

Benefits: immediate inspectable delivery, real browser interaction tests, bounded runtime model validation, shared implementation, no CDN or commercial runtime dependency for these examples. Source and compiled output are both retained.

Tradeoffs: this is a change from the original all-React/third-party-engine direction; DOM event wiring and styles need additional review, React lifecycle integration is not yet tested, and bounded native implementations do not automatically deliver enterprise grid/scheduling/chart features. It is not a claim that custom controls are preferable to mature libraries everywhere.

The adapter owns mounting and change events; application code owns API persistence and authorization. The Lab iframe contains document-level styles. Direct embedding needs deliberate CSS isolation. Advanced libraries remain evaluation candidates in the retained scope, with license, performance, accessibility and company compatibility gates.

Revisit after React/Storybook execution: retain a wrapper only where it meets the same contracts with less duplicated work. Replace internals when a supported upstream engine improves correctness, but keep model interfaces, synthetic fixtures and behavioral tests as the migration contract.
