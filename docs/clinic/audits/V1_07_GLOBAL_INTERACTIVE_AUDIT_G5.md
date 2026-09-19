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
