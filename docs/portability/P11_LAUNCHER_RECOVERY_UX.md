# P11 — Launcher & Recovery UX

**Status:** ACTIVE — BEFORE + visual reference locked. **0 EP credited.**

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

### Visual findings

Startup BEFORE: **5.6/10**.

- visually clean but lifecycle-blind;
- wording `Patientez pendant le demarrage de l'IA...` does not describe the actual local runtime lifecycle;
- there is no visible failure/recovery state;
- mobile wraps the long startup message awkwardly.

Security / Guided Restore BEFORE: **7.7/10**.

- strong hierarchy and responsive layout;
- safe actions are already visible;
- restore explanation is dense;
- lifecycle is not visible as a short progress model;
- `preflight`, `smoke check` and `rollback` are implementation terms rather than decision language.

## Visual reference locked before implementation

A desktop + 390 px mockup was rendered and inspected before product implementation.

Reference hashes:

- startup desktop: `f82cb5664b5fac895ffa835d76deedc3fcaefac0dee0987ae9adf278b3454441`;
- startup 390: `9ad33baa4972482df0f0b39de883af5594869e2eb442514e5682f3b131e9d4ea`;
- restore desktop: `baf199057b8a6db09d0498111c3f89cf43766a29a86ff92e34f6b76ef2a059e8`;
- restore 390: `f60fc719a753d2b135be6be59a18a78d05f52ef37c5489f1766f5c97fdc58a7e`.

### Launcher recovery wireframe

```text
DIGITAL CROWN

+----------------------------------------------------+
|  [ Démarrage interrompu ]                         |
|                                                    |
|  Digital Crown n'a pas pu démarrer                |
|  Le service local n'est pas devenu disponible.    |
|                                                    |
|  ✓ Cet écran ne lance aucune restauration,        |
|    suppression ni réinitialisation du cabinet.    |
|                                                    |
|  Etat      Runtime local indisponible              |
|  Code      RUNTIME_NOT_READY                       |
|  Journal   .../DigitalCrown/logs/digitalcrown.log |
|                                                    |
|  [ Réessayer l'ouverture ] [ Copier le journal ]  |
+----------------------------------------------------+
```

Mobile: the title wraps to two lines and both actions stack full-width at >= 48 px.

### Guided Restore wireframe

```text
Restauration guidée                         ACTION SENSIBLE
Digital Crown vérifie d'abord la sauvegarde et crée un secours.

[✓ 1 Analyse] [2 Secours] [3 Restauration] [4 Vérification]

+----------------------------------------------------+
| Étape suivante : créer le point de secours         |
| Aucune donnée active n'est modifiée à cette étape. |
|                         [ Préparer la restauration ]|
+----------------------------------------------------+
```

Mobile: 2 x 2 step grid, then one full-width primary action.

## Restore format boundary

The standard Guided Restore picker posts to `/admin/restore/preflight` and therefore accepts only its standard backup formats (`.enc`, `.zip`, `.dcbackup`).

Portable cabinet bundles (`.dcbundle`) are a separate migration flow: `/admin/restore/portable/preflight` requires a `migration_secret`. P11 must not advertise `.dcbundle` through the standard picker until that dedicated UX exists.

## Product constraints

- retain the existing Guided Restore backend/state machine;
- startup recovery must remain available even if the FastAPI application never becomes healthy;
- the recovery surface must not depend on Vercel or another remote service;
- do not expose secrets or stack traces;
- log path may be displayed, but log content is not rendered automatically;
- no Vercel deployment.
