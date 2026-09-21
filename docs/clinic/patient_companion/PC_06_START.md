# PC-06 — Patient Finance — START

Status: AUDIT COMPLETE — READ-ONLY FINANCE PROJECTION AUTHORIZED; ONLINE PAYMENT PROVIDER GATED
Branch: feature/patient-companion-pc06-finance
Base: master@09dd2de6f97bd276ebe140137cad51f3d8c1a010
Deployment: none

## Goal
Expose Patient Companion finance from the cabinet's authoritative financial records, without creating a second source of financial truth.

## Canonical scope
- online payment — GATED until a real provider + durable confirmation path is selected;
- payment schedules / échéanciers — read projection of existing InstallmentPlan/Installment;
- payment history — read projection of visible Payment rows;
- invoice retrieval — existing Note d'honoraires + Patient Companion document-share boundary.

## Architecture decision
See `PC_06_FINANCE_ARCHITECTURE_MAP.md`.

Do not reuse `GET /patients/{patient_id}/financial-snapshot` for Patient Companion: its current totals/history are not filtered with all active-accounting visibility rules.

PC-06 implementation path:
- use `principal_for_access()` for identity + tenant + patient ownership;
- derive billed amounts from active `Acte` rows;
- derive collected amounts/history from `Payment` with `accounting_service._visible_payment_filter()`;
- project existing `InstallmentPlan` / `Installment`, excluding schedules linked to trashed Actes;
- expose only active/latest Note d'honoraires documents already shared to that Patient Companion context;
- add no finance ledger/table for the read projection.

## Success — locked after primitive audit
- patient sees only finance records belonging to the active authorized tenant+patient context;
- amounts/statuses reconcile with active cabinet-side financial rows;
- hidden/voided/trashed generated payment effects are excluded;
- invoice retrieval reuses canonical document ownership/share/revocation semantics;
- edit/delete propagation cannot leave stale patient-facing totals or invoices;
- payment state is never shown as paid/settled/refunded before durable authoritative confirmation;
- no parallel finance ledger or dual-write path;
- online payment remains fail-closed until provider integration exists;
- UI passes responsive/accessibility evidence at the required mobile viewports.

## Proof — required
- architecture map: `PC_06_FINANCE_ARCHITECTURE_MAP.md`;
- backend reconciliation and isolation tests;
- invoice share/revocation tests;
- installment visibility tests;
- frontend truth-boundary tests;
- BEFORE -> target -> implementation -> AFTER same viewports;
- Chromium + WebKit 360x800 / 390x844;
- exact-head CI;
- double check;
- adversarial triple check;
- explicit human visual approval.

## Dependency
PR #644 / `fix/honoraires-cross-surface-reconciliation-20260920` contains concurrent honoraires trash/reconciliation hardening. Do not duplicate it. Re-verify equivalent behavior before PC-06 closeout.

## Next exact
Implement the read-only finance projection service/router + tests. Then implement the UI. Keep online payment action absent until a real provider is selected and its idempotent durable confirmation contract is defined.
