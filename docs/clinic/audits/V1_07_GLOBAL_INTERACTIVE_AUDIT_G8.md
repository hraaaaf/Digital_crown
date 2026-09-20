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

### Cloud telemetry fail-closed
`frontend/src/telemetryPolicy.g8Interactive.test.ts`
- Sentry DSN alone does not activate cloud telemetry;
- only exact explicit opt-in + non-empty DSN enables it;
- missing/blank DSN remains disabled.

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

## Inherited remediation state
- G1 Landing geography truth defect is remediated in code/tests; matched visual proof remains pending.
- G6 LicenseStatus hardcoded-plan defect is remediated in code/tests; matched visual proof remains pending.
- G7 Stock read/delete/mutation-refusal defects are remediated in code/tests; matched visual proof remains pending.

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

Inherited product defects are remediated. G8 remains uncertified until exact-head tests/build and the required G1/G6/G7 matched visual evidence are green.

## Pre-freeze adversarial inheritance
The separate canonical `docs/clinic/audits/V1_07_PREFREEZE_TRIPLE_CHECK.md` remains an independent release-safety prerequisite. It covers non-interactive security/runtime boundaries that this interactive denominator must not pretend to certify, including media tenant ownership, OAuth state/CSRF, cabinet LAN/TLS/cookies, telemetry opt-in, backup/document confinement, mobile/auth bounds and release dependency/runtime integrity.

These checks do **not** inflate the interactive-control denominator. However, V1-08 remains blocked until the final candidate also satisfies the pre-freeze exact-head/runtime gates recorded in G10.


## Browser adversarial escalation
A dedicated real-Chromium transverse gate now complements the existing component evidence:
- representative compact/desktop reachability with no horizontal overflow;
- Stock read-error ≠ empty truth in-browser;
- destructive confirmation dialog focus ownership + Escape close;
- refused delete preserves visible state;
- representative Stock create mutation is single-flight under double activation.

Harness: `frontend/scripts/certify-v1-07-g8-browser-adversarial.mjs`.
Workflow: `.github/workflows/v1-07-g8-browser-adversarial.yml`.
G8 remains uncertified until this exact-head browser gate and inherited G1→G7/G4 gates are green.
