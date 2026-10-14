# V1.5-07A — Theme Packs & Motion: foundation / isolation contract

Status: DRAFT / CONTRACT-ONLY / NOT IMPLEMENTED  
Repository: `hraaaaf/Digital_crown`  
Baseline: `master@9158902e034c22b162873d5fd44ea7afd45f3e16` (2026-10-14)  
Canonical product decision: [V1.5-07 Theme Packs & Motion](https://app.notion.com/p/3e677c66336281639049f4cc7be1e5ae)  
Parallel work: [LOT06 acquisition PR #851](https://github.com/hraaaaf/Digital_crown/pull/851) remains OPEN/DRAFT.

## 1. Purpose and non-goals

Make three **visually distinct** product families available without changing any workflow, permissions, clinical meaning, or patient data:
1. Clinical Minimal;
2. Color / Friendly;
3. Premium Motion.

This first PR deliberately **does not enable** any pack, expose a new user setting, alter CSS, change persistence, modify UI, run or certify visual screenshots, or imply that the three packs are already implemented. It establishes a reviewable boundary and a concrete acceptance matrix so subsequent PRs can implement the smallest safe slice.

Excluded: LOT06 hot-folder, imaging gateway, hardware, LOT04/05 imports, queue/LOT08, Station functional behavior, external cloud data transfer, clinical algorithms, DB migrations, and unapproved 07.1 **MultiView Studio** (proposal only).

## 2. Existing baseline — do not create a second theme engine

Repository source observations on baseline master (code inspection, not runtime validation):
- `frontend/src/index.css`: existing `:root` semantic tokens; `[data-theme='emerald'|'rose'|'prestige'|'ocean'|'graphite'|'dark'|'high-contrast']` selectors; `@theme` bridge; reduced-motion rule.
- `frontend/src/features/admin/Settings/tabs/branding/presets.ts`: current preset-to-`selected_theme` mapping and density defaults.
- `frontend/src/features/admin/Settings/hooks/useSettingsStore.ts`, `frontend/src/features/admin/Settings/types.ts`: current settings read/write representation.
- `backend/models.py`, `backend/schemas/cabinet.py`: existing `selected_theme`, default `elite`. No new schema required for foundation.
- `frontend/src/features/mobile/Dashboard/hooks/useMobileRuntimeTheme.ts`: independent mobile consumer of clinic theme values, which must stay compatible.
- `frontend/src/styles/patientCompanionTheme.css`, `frontend/src/features/mobile/mobileRuntimeTheme.css`: mobile/patient surfaces already consume shared tokens.

The three V1.5 pack families are **product-level design choices**. They are not yet proven to map one-to-one to existing `selected_theme` IDs. Do not silently overwrite legacy values, reinterpret `prestige` as motion policy, or store an unrecognized pack name in a field accepted by existing clients.

## 3. Architecture contract for 07B+

**One source of theme truth.** Preserve clinic settings, existing selectors, token naming, and known legacy IDs. Any new family-to-preset mapping must have a documented compatibility table and explicit legacy fallback tested on desktop and Pocket. In absence of full backwards compatibility, use an adapter rather than replacing `selected_theme` semantics.

**Tokens versus clinical states.** Cosmetic choices may affect surface, background, typography, radius, elevation, non-clinical accents and density. Clinically meaningful danger/warning/success/info semantics remain explicit; textual status, iconography and actions cannot rely solely on color. Tokens must be WCAG-readable under every pack.

**Pack is not authority.** Theme/density/motion preferences never change route visibility, RBAC, audit, API permissions, patient media access, clinical calculations, persistence rights, or appointment/financial state. No pack-specific duplication of business components.

**Motion is independently controllable.** A pack must work when animations are fully disabled. `prefers-reduced-motion: reduce` is a hard accessibility constraint. No motion-dependent interaction, forced transitions, or loss of focus indication.

**Preview and rollback.** A preview never silently persists. On cancel/failure, restore the exact previous `selected_theme` and relevant style/font/density state; on reload, persisted settings must be explicit and reversible. Handle offline/unavailable settings API without falsely reporting successful save. Specify authorization and ownership before any write.

**Local-first / remote assets.** Theme presentation cannot introduce transfer of patient data or new external network dependencies. Audit preexisting remote font imports before any release readiness claim. Treat high-contrast mode and text scaling as supported product paths, not a fourth branded family.

**Surfaces.** Include Cabinet desktop, Hub (neutral Digital Crown chrome), Station (touch suitable), Pocket/mobile (only the routes where theming currently exists), and Patient Companion where its current inherited token model applies. Preserve their separate authorization boundaries.

## 4. Acceptance / evidence matrix (future implementation, not checked by this PR)

| Required check | Observation / failure mode | Gate |
| --- | --- | --- |
| Legacy theme compatibility | Current `elite`, `emerald`, `rose`, `prestige`, `ocean`, `graphite`, `dark`, `high-contrast` render correctly; unknown IDs fail to a safe supported default | REQUIRED |
| Theme invariant | Compare same authorized workflow/API transitions in all 3 families; no RBAC/clinical-state delta | REQUIRED |
| Mobile support | Confirm which Pocket/Patient Companion/Station routes exist; no invented mobile features; capture applicable surfaces | REQUIRED |
| Visual BEFORE/TARGET/AFTER | Compare real screenshots at **390, 430, 768, 1280 px**, same routes and states, for each implemented family | REQUIRED |
| Accessibility | WCAG 2.2-oriented review, keyboard focus, contrast, label semantics, 200% zoom/text scale, reduced-motion, touch targets | REQUIRED |
| Persistence / reversal | Preview is transient; cancel/refresh/API error and post-save rollback preserve correct state | REQUIRED once persistence is modified |
| Motion | `prefers-reduced-motion` and manual motion-off both remove nonessential animations without disabling controls | REQUIRED once motion is modified |
| Reliability/privacy | No patient payloads in theme telemetry/logs; offline/failed API does not claim save | REQUIRED once settings change |
| Performance | Measure script/layout costs on representative mobile + desktop and report baseline/AFTER | REQUIRED once UI is modified |
| Extra screenshot modes | Dark/high contrast and Arabic/FR/EN where relevant | REQUIRED for affected surface |
| CI/evidence | Tests collected/executed on the exact PR HEAD, record skips and artifact links, two adversarial perspectives and clean confirmation | REQUIRED before lot closure |

No screenshots, test runs, CI green status or independent human reviews are asserted by this contract-only commit.

## 5. Work sequencing / change control

- **07A (this DRAFT PR)**: baseline contract and isolation only.
- **07B**: implement *one* mapped pack/prototype with a compatibility adapter and negative tests; collect real BEFORE/TARGET/AFTER evidence. No auto-save at this stage.
- **07C**: add the other visual families and separately controllable motion/reduced-motion, with functional parity proofs.
- **07D**: preview/persistence/rollback and a11y/performance gate after required authorization and tests.
- **07E**: multi-viewport review, independent verification when available, closeout/merge only by separate decision.

Do not touch `tools/imaging_gateway/`, LOT06 docs/workflow, clinical backend, DB/Alembic, imported customer data, or deployment configuration as a shortcut. Begin every implementation slice by checking latest `master`, branch HEAD, exact changed-file list, and current relevant CI; isolate additional work if another PR modifies the same theme settings paths.

## 6. Stop conditions

Block release/merge if a theme can misstate a clinical warning, break high-contrast/reduced-motion, alter access controls, lose a persisted setting, render a Pocket flow unusable, or if the acceptance proof is missing. The LOT07 theme visual gate is **NOT SATISFIED** by this documentation PR.

No Vercel deployment, master merge, production install or release activation is authorized by this document.
