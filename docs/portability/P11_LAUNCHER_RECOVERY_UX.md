# P11 — Launcher & Recovery UX

**Status:** CLOSED ✅ — **8/8 EP credited.**

## Goal

Expose truthful, actionable lifecycle and recovery states without requiring a console.

### Startup

Replace the ambiguous/silent startup failure path with an explicit recovery surface:

- `starting -> ready` stays automatic;
- if the local runtime does not become ready, show a recovery surface instead of silently doing nothing;
- state a stable reason code and the local log path;
- state precisely that the recovery surface itself launches no restore, deletion or cabinet reset, without claiming that the preceding startup sequence made no data change;
- expose a safe retry/open action and a log-path copy action;
- no destructive recovery action.

### Guided Restore

Keep the existing restore engine and safety contract, but make its lifecycle immediately scannable:

`Analyse -> Secours -> Restauration -> Verification`

Technical terms such as `preflight`, `smoke check` and `rollback` must not be the primary wording used when the dentist has to decide what to do next.

## Success criteria

- no console required for startup/recovery decisions;
- no invented state: UI derives from the real lifecycle state;
- mobile actionable controls >= 44 px;
- no horizontal overflow at 1440 / 1024 / 768 / 430 / 390;
- zero page/runtime error in the visual harness;
- same surfaces captured BEFORE and AFTER;
- no additional destructive action;
- visual score assigned only after AFTER inspection.

## BEFORE — verified 2026-08-24

- branch: `portability/p11-before`;
- commit: `ff7365ff3778c2f9f9634941721473baf24ad3e6`;
- draft baseline PR: `#240` — must not be merged as product work;
- workflow: `Portability P11 Launcher Recovery BEFORE`;
- run: `32780649466` — SUCCESS;
- artifact: `portability-p11-before`, id `9539649740`;
- artifact digest: `sha256:02203a2ca6710172b9ee882d6bc3a17dae536866444f5d9b08afee273ae54c62`;
- proof cardinality: 10 screenshots = 2 surfaces x 5 viewports;
- overflow/runtime guards: PASS.

### Visual findings BEFORE

Startup BEFORE: **5.6/10**.

- visually clean but lifecycle-blind;
- wording `Patientez pendant le demarrage de l'IA...` did not describe the actual local runtime lifecycle;
- no visible failure/recovery state;
- mobile wrapped the long startup message awkwardly.

Security / Guided Restore BEFORE: **7.7/10**.

- strong hierarchy and responsive layout;
- safe actions already visible;
- restore explanation dense;
- lifecycle not visible as a short progress model;
- `preflight`, `smoke check` and `rollback` were implementation terms rather than decision language.

## Visual reference locked before implementation

Reference hashes:

- startup desktop: `f82cb5664b5fac895ffa835d76deedc3fcaefac0dee0987ae9adf278b3454441`;
- startup 390: `9ad33baa4972482df0f0b39de883af5594869e2eb442514e5682f3b131e9d4ea`;
- restore desktop: `baf199057b8a6db09d0498111c3f89cf43766a29a86ff92e34f6b76ef2a059e8`;
- restore 390: `f60fc719a753d2b135be6be59a18a78d05f52ef37c5489f1766f5c97fdc58a7e`.

## Restore format boundary

The standard Guided Restore picker posts to `/admin/restore/preflight` and therefore accepts only its standard backup formats (`.enc`, `.zip`, `.dcbackup`).

Portable cabinet bundles (`.dcbundle`) are a separate migration flow: `/admin/restore/portable/preflight` requires a `migration_secret`. P11 does not advertise `.dcbundle` through the standard picker.

## Product implementation verified

- local, self-contained recovery HTML independent of FastAPI health;
- reason codes `RUNTIME_NOT_READY`, `RUNTIME_START_FAILED`, `INSTANCE_NOT_READY`;
- truthful recovery copy: the screen itself performs no restore, deletion or reset;
- retry/open + copy-log-path actions;
- Guided Restore lifecycle exposed as `Analyse -> Secours -> Restauration -> Vérification`;
- primary action wording no longer depends on implementation jargon;
- mobile P11-critical controls >= 44 px;
- `.dcbundle` removed from the standard restore picker.

## AFTER — verified 2026-08-24

Exact candidate:

- branch: `portability/p11-launcher-recovery-ux`;
- candidate HEAD: `cbaf21a066fb6b8b70f4c9d6b3ec1a950cda890b`;
- PR: `#241`;
- one P11 product commit over base P10 `0fa22fda40881f0823a038d694262cd43c9b43d2`.

Final certification:

- workflow: `Portability P11 Launcher Recovery UX`;
- run: `32783305559` — SUCCESS;
- `P11_LAUNCHER_RECOVERY_CONTRACT=SUCCESS`;
- targeted runtime supervisor tests: **8 passed**;
- frontend production build: SUCCESS;
- artifact: `portability-p11-after`, id `9540590729`;
- artifact digest: `sha256:47ffdcee25d9237ac89f9665c2a0d34603005b8b2786412b63eb30f2a0457cf1`;
- 15/15 AFTER screenshots: startup + security + security-prepared at 1440 / 1024 / 768 / 430 / 390;
- all 15 health entries: `scrollWidth == clientWidth`, `errors: []`;
- P11-critical mobile controls >= 44 px.

Regression evidence on exact candidate:

- Portability Runtime `32783305528` — SUCCESS;
- T2 Runtime Browser `32783305594` — SUCCESS;
- Catalog Connected Truth `32783305574` — SUCCESS;
- Patient P7 Final `32783305575` — SUCCESS;
- Settings RBAC Visual `32783305530` — SUCCESS;
- Settings Security Visual `32783305489` — SUCCESS;
- CI `32783305627` — SUCCESS.

Non-P11 failure explicitly excluded from P11 credit:

- P6 Windows Packaging `32783305531` failed its pre-existing static packaging gate on `DigitalCrown.spec`: `forbidden spec content: .env`;
- P11 did not modify `DigitalCrown.spec`; this remains a P6 blocker, not a P11 regression.

## Visual validation

Comparison BEFORE -> mockup -> AFTER was inspected on the matching surfaces and critical viewports.

- Startup recovery AFTER: **9.3/10** (BEFORE 5.6/10).
- Guided Restore AFTER: **9.1/10** (BEFORE 7.7/10).

Observed residual:

- the prepared restore state is intentionally information-dense at 390 px, but remains readable, decision hierarchy is preserved, and there is no horizontal overflow.

## Merge

- PR `#241` merged into `portability/p10-update-engine`;
- merge commit: `455e7603c78b0139c0b39e217bed768bfe1186e7`;
- this does **not** claim that P10 or `master` are closed;
- no Vercel deployment.
