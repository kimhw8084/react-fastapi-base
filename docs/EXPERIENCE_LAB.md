# Experience Lab: implementation and integration

## Two execution surfaces, one widget implementation

`experience-lab/src` contains strict-TypeScript custom elements using DOM/SVG. `public/lib` contains their compiled ES modules and declarations. `python3 dev lab` serves that exact build without external dependencies. `frontend/src/platform/engineering/EngineeringWidget.tsx` adapts the same elements to React; it does not create a second implementation.

The `/lab` route in the React host embeds the Lab in a same-origin iframe. Its stylesheet and document-level theme do not leak into the application shell. Direct `EngineeringWidget` use requires the consuming app to intentionally import/contain widget styles. The supplied stylesheet is not yet a fully isolated CSS package. The React host, Storybook build, and browser smoke workflow are runtime-certified in the current evidence set; manual accessibility certification remains a separate gate.

## Data ownership

A widget receives a cloned model via `configure(model, options)`. Public models are runtime-validated before rendering, not merely asserted through TypeScript. Actions emit `model-change` intent, including a new model, and selection events where relevant. The caller owns persistence, authorization, revision checks, server validation, idempotency and conflict recovery. Lab `readOnly` is a demonstration setting, never an authorization boundary.

The Lab stores appearance preferences locally when browser storage is available. Sample business models are held in memory for the browsing session. Refreshing does not persist component mutations to FastAPI. Synthetic fixtures contain no company identities or production equipment data.

## React example (integration source; requires the unresolved React toolchain)

```tsx
<EngineeringWidget
  kind="gantt"
  value={tasks}
  presentation={{
    schedule: { startDate: '2027-01-01', days: 60 },
    locale: 'en-US',
  }}
  readOnly={!permissions.canEdit}
  onChange={(intent) => saveThroughYourApi(intent)}
/>
```

Model-specific typing is retained through the `kind` discriminator. API failure handling is application-owned; do not silently accept the local intent as a committed transaction. Gantt supports bounded finish-to-start checks, not full critical-path/resource optimization.

## Presentation and extension

- Semantic tokens in styles.css drive light/dark, status colors, density and reduced motion.
- `presentation.ts` adds typed optional titles/locales, schedule origin/horizon, rack capacity/power budget, wafer labels/units.
- Actual application business metadata is feature-owned. Default examples intentionally contain human-readable synthetic labels.
- Wafer coordinates are screen-oriented: positive X right, positive Y down. Real substrate/reticle/bin semantics require explicit adapters.
- Topology is a viewer; pipelines demonstrate local state, not executable workflows.
- Process charts show configured limits and basic sample statistics; no complete SPC rule engine or metrology validation is asserted.

## Component catalog

`src/registry.ts` owns the 23 widget family definitions. `scripts/catalog.py` generates `catalog/components.json` and the coverage document. `catalog/examples.json` contains browser-extracted, runtime-validated example models used by Storybook; it is not another hand-maintained business schema.

`catalog/roadmap.json` retains the expanded 605-entry scope, including variants and platform services. Each entry is backed by a generic family renderer/contract and the generated registry test; domain-specific production qualification remains tracked in `docs/v1-completion-status.json`. `scripts/catalog.py --check --release` passes against the current source.

## Storybook

`frontend/.storybook` and `frontend/stories/Engineering.stories.tsx` provide 23 controlled React stories plus theme/density toolbar configuration. The pinned dependencies are installed from `package-lock.json` and the current `build:storybook` gate passes:

```bash
cd frontend
npm ci
npm run build:storybook
```

The standalone Lab remains usable without Storybook. A Storybook source file is not a passing interaction/a11y test.

## Verification and limits

The delivered browser harness tests the exact compiled modules. In this environment it used `--mode in_memory`: modules are mapped to Blob URLs to exercise the code in Chromium without changing managed browser policies. HTTP content/security/path handling is separately tested against real server sockets. Default `http` mode starts a real local server on the target machine.

The current React browser run exercises the application against a disposable FastAPI backend and reports zero browser console errors in its tested workflows. It does not certify Safari/WebKit/Firefox behavior or full WCAG conformance; axe plus manual keyboard, zoom, contrast and VoiceOver evidence remain release gates.
