# Digital Crown V1-07 — Global Interactive Audit — G5

Status: IN PROGRESS

## Goal
Certify cabinet administration surfaces: Settings, profile/branding/agenda/catalog/runtime preferences, security, backup/restore, team management and practitioner context.

## Success
- every Settings tab/control is mapped to behavioral proof;
- staged/shared save behavior is proved;
- read failures fail closed and retry truthfully;
- backup export and restore preflight/prepare/apply/cancel are proved with exact mutation gates;
- team create/approve/reject/status/delete/permissions reuse LOT2 proof only where behavior is identical;
- exact-head frontend tests + build are green before certification.

## Verified surfaces

### Settings shell
`frontend/src/features/admin/Settings/SettingsContainer.tsx`
- permission-gated tabs;
- shared save bar for profile-backed tabs;
- dirty-state warning;
- profile read failure + retry;
- Team read-truth gate.

### Settings tabs
- ProfileTab
- BrandingTab
- CatalogTab
- AgendaTab
- IATab / runtime preferences
- SecurityTab / backup-restore
- TeamManager

### Backup / restore safety contract
`frontend/src/features/admin/Settings/tabs/SecurityTab.tsx`
- export: GET `/admin/export-db` blob;
- preflight: POST `/admin/restore/preflight` multipart, no active mutation;
- prepare only from compatible `preflight_ready`;
- apply only from `prepared` and exact confirmation `RESTAURER`;
- status polling terminates on success / rolled_back / rollback_failed / blocked;
- cancel DELETE only when restore is not in-flight.

### Reusable team proof
`frontend/src/features/admin/TeamManager.buttonMatrix.test.tsx`
Existing LOT2 behavioral proof covers create, approve, reject, suspend/reactivate, delete, permissions, errors and anti-double-action. Reuse is allowed only if current implementation remains behaviorally identical.

## Certification gate
Do not certify G5 until:
1. Settings/backup/restore missing matrices are added;
2. TeamManager reuse is reconciled against current source;
3. exact-head frontend tests + build pass;
4. evidence is recorded here and in Notion.


## Behavioral proof

1. `frontend/src/features/admin/Settings/SettingsContainer.g5Interactive.test.tsx`
   - permission-gated settings tabs;
   - tab switching;
   - shared dirty/save bar;
   - profile read failure fail-closed + retry;
   - failed save keeps dirty state.

2. `frontend/src/features/admin/Settings/tabs/SecurityTab.g5Interactive.test.tsx`
   - verified backup export;
   - restore preflight multipart with no destructive mutation;
   - incompatible backup blocks prepare/apply;
   - prepare gate;
   - exact RESTAURER confirmation;
   - apply + terminal status;
   - cancel/delete;
   - preflight refusal.

3. `frontend/src/features/admin/Settings/tabs/IATab.g5Interactive.test.tsx`
   - performance mode;
   - contextual clinical tips;
   - patient indicators;
   - all stage dirty runtime preferences before shared save.

4. `frontend/src/features/admin/Settings/tabs/AgendaTab.g5Interactive.test.tsx`
   - backend schedule truth;
   - staged weekday changes;
   - overlap validation before mutation;
   - save/refusal;
   - closure add/delete with explicit confirmation.

5. `frontend/src/features/admin/Settings/tabs/CatalogTab.g5Interactive.test.tsx`
   - specialty create;
   - act create/edit/deactivate;
   - invalid tariff blocking;
   - pathology create/edit/deactivate;
   - read failure + retry;
   - refused mutation keeps modal.

6. `frontend/src/features/admin/Settings/tabs/ProfileTab.g5Interactive.test.tsx`
   - cabinet identity staging;
   - specialty/header regeneration;
   - contact controls;
   - logo upload/delete;
   - explicit save/refusal;
   - employee practitioner identity lock.

7. `frontend/src/features/admin/Settings/tabs/BrandingTab.g5Interactive.test.tsx`
   - preview scope is non-mutating;
   - preset staging;
   - reset confirmation;
   - animated background runtime preference.

8. `frontend/src/features/clinic/ClinicPractitionerBar.g5Interactive.test.tsx`
   - multi-practitioner backend truth;
   - explicit practitioner selection;
   - owner fallback;
   - secretary employer fallback.

## Reused current-code proof

`frontend/src/features/admin/TeamManager.buttonMatrix.test.tsx` remains behaviorally aligned with current TeamManager implementation and covers:
- GOLD / PREMIUM / ELITE quotas;
- member create;
- backend quota refusal;
- approve / reject;
- suspend / reactivate;
- permissions save;
- permanent delete;
- load error + retry;
- modal close;
- anti-double-action;
- mutation error surfacing.

G5 functional surfaces inspected are now mapped to behavioral proof. Certification still requires exact-head frontend tests + build.


## Functional reconciliation
All currently identified G5 interactive surfaces are mapped to behavioral proof or verified LOT2 reuse.

Status: FUNCTIONALLY RECONCILED — CERTIFICATION PENDING EXACT-HEAD TESTS + BUILD.
