# V1-07 G6/G7 — Truth & Safety UI Target

## BEFORE — verified source defects

### LicenseStatusPage
Current expired copy hardcodes:
> Votre licence Elite a expiré…

But the current `AppUser` contract used by this page exposes no subscription-plan truth. The page therefore cannot truthfully name the expired pack.

### StockPage
1. A failed `/stock/items` read falls through to `items = []` and can visually claim “Aucun article”.
2. Permanent deletion is dispatched directly from the trash control without explicit confirmation.
3. Add/edit/quantity/delete failures have no explicit user-facing refusal state.

## Goal
Make licence/stock UI truth-preserving and destructive-stock actions explicit without changing navigation or business endpoints.

## Success
- expired licence copy is plan-neutral;
- stock read failure renders an explicit unverified/error state with Retry;
- stock delete requires an explicit in-app confirmation dialog;
- cancel is non-mutating;
- delete refusal keeps the article and dialog, with explicit backend/generic error;
- quantity/add/edit refusal is visible and no false success is shown;
- matched BEFORE/AFTER screenshots exist at the same viewports;
- exact-head tests/build are green.

## Target reference / mock

### Expired licence target
Title: **Licence Expirée**

Body:
> Votre licence a expiré le DD/MM/YYYY. L'accès aux fonctionnalités cliniques est suspendu.

Buttons unchanged:
- Renouveler maintenant
- Retour à la connexion

### Stock read-error target
Keep the page shell, replace the table/empty area with:
- warning icon;
- title **Stock indisponible**;
- copy **Impossible de confirmer le contenu du stock. Aucun état vide n’est affiché tant que la lecture n’a pas réussi.**
- button **Réessayer**

### Stock delete-confirmation target
In-app dialog:
- title **Supprimer cet article ?**
- copy identifies article;
- **Annuler**;
- destructive **Supprimer définitivement**
- backend refusal appears inside the dialog and keeps it open.

### Stock quantity refusal
Visible compact alert above the table:
- **Action stock non enregistrée**
- backend detail when available, otherwise stable generic wording.

### Stock add/edit refusal
Visible error inside the add/edit modal:
- backend detail when available;
- modal remains open;
- no false success or premature close.

### Stock delete refusal
The confirmation dialog remains visible after backend refusal and shows the refusal detail; the article stays present.

## Visual evidence
Use deterministic Playwright harness.
Matched viewports:
- 390 × 844
- 768 × 1024
- 1440 × 1000

Scenarios:
- expired licence;
- stock read failure;
- stock delete confirmation;
- stock quantity refusal;
- stock add refusal;
- stock delete refusal.

True BEFORE must be captured from the PR base SHA with the audit-only harness copied into the baseline worktree.
AFTER must be captured from exact PR HEAD.


## Additional G1 blocker — Landing geography truth

### BEFORE — verified source defect
The public Landing currently says:
> DigitalCrown centralise patients, agenda, facturation et dossiers cliniques dans une interface moderne conçue pour les dentistes algériens.

This conflicts with the current product market/currency context (Morocco / MAD).

### Goal
Correct the geography claim without changing layout or CTA hierarchy.

### Target
> DigitalCrown centralise patients, agenda, facturation et dossiers cliniques dans une interface moderne conçue pour les dentistes marocains.

### Success
- no `dentistes algériens` remains on the Landing;
- `dentistes marocains` is visible in the same hero location;
- same matched BEFORE/AFTER viewports are captured;
- no horizontal overflow or runtime error is introduced.

### Visual scenario
Add `landing-geography` to the truth-safety visual harness at:
- 390 × 844
- 768 × 1024
- 1440 × 1000
