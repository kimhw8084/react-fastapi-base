# CHG-6 R1 rendered UIQA evidence

- Project: `react-fastapi-base`
- Change: `CHG-6`, iteration `1`
- Exact base: `68b55ee1dd3fda00d8899682b4f8a09733f3dd0b`
- Work branch: `codex/CHG-6-r1`
- Source commit for after-capture: `ef5c7e2d713d5ab424bf3a076764e0cd594b13bb`
- Resulting candidate: `1.0.0-rc.7`
- After-capture: [`CHG-6-r1-rendered.json`](./CHG-6-r1-rendered.json)

All contrast values below are browser-computed foreground/background colors using the WCAG relative-luminance ratio. The after capture exercises light, dark, and high-contrast states. The app capture also records grid geometry/rows and Saved View checkbox geometry.

| UIQA | Disposition | Bound-source reproduction and root cause | Correction and regression evidence |
| --- | --- | --- | --- |
| 001 | `REPRODUCED_ROOT_DEFECT` | Dark Operations primary action rendered `#06111f` on `#25598f`, `2.62:1`. The shared dark `--accent-contrast` token was too dark for the shared primary/selected controls. | `frontend/src/theme/tokens.css` sets the dark accent contrast to white. After: `7.23:1` in `app.darkOperationsAccent` in the JSON. Covered by `frontend/tests/e2e/uiqa.spec.ts` in dark Operations. |
| 002 | `REPRODUCED_ROOT_DEFECT` | `DataGrid.tsx` used the AG Grid v36 legacy theme API plus `ag-theme-alpine` legacy CSS; dark rows/root rendered white with dark text. | `frontend/src/platform/grid/DataGrid.tsx` now owns a shared `themeAlpine.withParams(...)` configuration using platform semantic tokens; legacy imports/props were removed from `frontend/src/main.tsx` and `frontend/src/theme/application.css`. After: dark root/row are `rgb(23,31,43)` with `rgb(238,243,250)` and 7 rows are rendered. The UIQA e2e test also checks light/high-contrast rows, virtualization-sized output, keyboard focus and selection behavior remains covered by existing grid tests. |
| 003 | `REPRODUCED_ROOT_DEFECT` | Native Saved View checkboxes expanded to `703×40px` and labels became columnar because broad shared input sizing and global label layout rules applied to checkbox controls. | `frontend/src/theme/application.css` adds type-specific native checkbox/radio geometry and row grouping; `frontend/src/platform/workspace/SavedViews.tsx` adds the semantic `check-label` hook. After: native inputs are `16×16px`, labels are flex rows. `frontend/tests/e2e/uiqa.spec.ts` checks role/name, focus and Space; existing workspace e2e covers persistence and save/delete flows. |
| 004 | `REPRODUCED_ROOT_DEFECT` | Lab light info badge used `--info:#356fc0` on `--info-soft:#e9f0fc`, `4.38:1`, below AA. | `experience-lab/public/styles.css` changes the light semantic info token to `#2f66ad`. After light-normal is `5.06:1`; all Lab theme/contrast minima are in the JSON and covered by `test_uiqa_shared_lab_semantic_contrast`. |
| 005 | `REPRODUCED_ROOT_DEFECT` | `experience-lab/src/scheduling.ts` rendered equipment timeline labels as `color:var(--page)` over several light fills: productive `3.85:1`, neutral `1.48:1`, maintenance `2.27:1`, engineering `3.43:1`; long labels also lacked overflow measurement. | Shared Lab label tokens and per-tone semantic label selectors were corrected in compiled `experience-lab/public/styles.css`; label spans now ellipsize within the measured state block. After all light/dark and high-contrast timeline state minima are ≥`4.80:1`; rendered coverage is in the Lab browser test and JSON. |
| 006 | `DERIVATIVE_OF_SHARED_ROOT` | Independently reproduced in `experience-lab/src/scheduling.ts` TraceWaterfall: it used the same page-color label rule, and the light info trace bar was `3.43:1`. | The shared Lab semantic label-token correction that closes UIQA-005 also owns `.trace-bar`; no feature-local screenshot color was added. After trace minima are `4.95:1` (light normal/high) and `7.98:1` (dark normal/high). Covered by the same Lab browser test and JSON. |
| 007 | `REPRODUCED_ROOT_DEFECT` | The app notification renderer is `frontend/src/features/system/Workspace.tsx` (`.system-list article small`) and consumed `--text-muted`; unread light timestamp was `4.39:1` on notice surface. The Lab notification renderer separately consumed low-emphasis `--subtle` and measured `3.97:1` on light. | `frontend/src/theme/tokens.css` raises the light app `--text-muted`; `experience-lab/public/styles.css` raises light `--subtle`. After app timestamp minima are `5.02:1` light, `4.54:1` dark, and `12.53:1` high contrast. Lab minima are `5.30:1`, `6.37:1`, `7.44:1`, and `9.61:1` across the four modes. Covered by the app notification fixture e2e and Lab browser test. |

## Scope and evidence notes

- UIQA-005 and UIQA-006 are derivative symptoms of one shared Experience Lab semantic label-color root; no React-side compensation was added.
- AG Grid remains AG Grid v36 with virtualization, selection, and keyboard behavior intact; only its supported v36 theme object and semantic token parameters changed.
- Saved Views remains native checkbox controls with existing persistence, auto-save, and error handling.
- `evidence/current/browser/` contains the updated deterministic app-state screenshots produced by the repository browser harness. `evidence/current/lab/verification.json` and `evidence/current/lab/uiqa-junit.xml` contain the Lab verification and focused rendered regression results.
- RC.6 remains the immutable historical base; these results qualify the changed RC.7 candidate only. Company PaaS per-request identity and company production qualification remain outside this Change.
