# Digital Crown V1-07 — Global Interactive Audit — G8

Status: IN PROGRESS

## Goal
Certify transverse/adversarial interaction behavior across previously audited surfaces: loading, true-empty vs unverified/error, offline, disabled, double-action resistance, refresh/back, permissions, responsive/accessibility and mutation non-success on API refusal.

## Success
- critical mutation controls are single-flight while in progress;
- error/unverified states are not presented as truthful empty states;
- destructive/refused mutations do not produce false success;
- offline state and queued actions are explicit;
- modal focus/escape/scroll behavior is accessible;
- responsive patient/dashboard contracts remain reachable on compact viewports;
- role/permission deep-link fail-closed proof is reconciled from G2/G5/G6;
- exact-head frontend tests + build pass.

## Reusable behavioral evidence

### Accessibility / modal behavior
`frontend/src/components/CrownDialog.g8Interactive.test.tsx`
- scroll lock + restoration;
- preferred autofocus + opener focus restoration;
- Escape close;
- Tab / Shift+Tab focus loop;
- closed state does not render/lock.

### Offline truth
`frontend/src/components/mobile/OfflineQueueViewer.g8Interactive.test.tsx`
- online/no queue;
- explicit offline state;
- queued mutation method/target truth;
- syncing state distinct from offline;
- offline with zero queued actions does not invent pending work.

### Responsive reachability
- `frontend/src/features/dashboard/dashboardD8Responsive.test.ts`
- `frontend/src/features/patients/PatientDossierResponsiveUX.ux1.test.ts`
- existing visual certification workflows for Dashboard/Patient/Settings/Agenda/Cephalo.

### Error vs empty / refusal / permissions
Reconciled from behavioral matrices across G1→G7, including:
- Patient list/create/edit/details;
- Dashboard waiting-room/alerts;
- Agenda/frontdesk/notifications;
- Document/payments/clinical/imaging;
- Settings/backup/team;
- SuperAdmin/licences;
- Marketplace/library.

## Open transverse defects inherited from prior gates
- G6 LicenseStatus hardcoded Elite wording remains unresolved under UI protocol.
- G7 Stock read failure/delete confirmation/mutation refusal UI defects remain unresolved under UI protocol.

## Certification gate
Do not certify G8 until:
1. anti-double-action proof exists for representative critical mutations;
2. cross-lot error/empty/refusal/permission evidence is reconciled;
3. exact-head tests + build are green;
4. inherited open product-truth defects are either remediated or explicitly block G9.


## Additional G8 proof

`frontend/src/test/CriticalMutationSingleFlight.g8Interactive.test.tsx`
- QuickPay submit becomes disabled after first dispatch and second click cannot dispatch a second payment;
- Frontdesk request creation is single-flight;
- RVG upload save is single-flight.

## Functional reconciliation
Cross-lot evidence now covers:
- true empty vs unverified/error states;
- mutation refusal without false success;
- permission/deep-link fail-closed;
- modal focus/keyboard/scroll accessibility;
- offline queued-action truth;
- compact responsive reachability;
- representative critical mutation single-flight.

Status: FUNCTIONALLY RECONCILED — CERTIFICATION PENDING EXACT-HEAD TESTS + BUILD.

Inherited blockers remain:
- G6 LicenseStatus hardcoded plan wording;
- G7 Stock read/delete/mutation-error defects.
These prevent G9 freeze until resolved.
