# PC-06 — Patient Finance — Architecture Map / Primitive Audit

Status: AUDIT COMPLETE — READ PROJECTION PATH IDENTIFIED; ONLINE PAYMENT PROVIDER NOT VERIFIED
Branch: feature/patient-companion-pc06-finance
Base audited: master@09dd2de6f97bd276ebe140137cad51f3d8c1a010
Related reconciliation work: PR #644 / branch fix/honoraires-cross-surface-reconciliation-20260920 (not integrated into this branch)
Deployment: none

## Goal
Expose Patient Companion finance from existing cabinet financial truth without creating another ledger, balance engine, or optimistic payment state.

## Canonical primitives verified

### Patient / tenant authority
- `Patient.employer_id` is the cabinet ownership boundary.
- Patient Companion access is bound by `PatientCompanionAccess(identity_id, employer_id, patient_id)`.
- `principal_for_access()` resolves an active, non-revoked Patient Companion context and joins Patient on both patient ID and employer ID.
- Any PC-06 query must scope every financial row through this principal, never only by patient ID.

### Billing truth
- `Acte` is the structured billing row used by accounting for active billed amounts.
- `Acte.document_archive_id` links rows generated from a Note d'honoraires to the parent `DocumentArchive`.
- Accounting already avoids double counting a Note d'honoraires JSON when linked Acte rows exist.
- `Acte.deleted_at` is the accounting-trash visibility boundary.

### Canonical financial document
- `DocumentArchive` with `document_type = NOTE_HONORAIRES` is the canonical archived invoice/fee-note document.
- It owns lifecycle/versioning, `status`, `is_latest_version`, `payment_status`, `is_collected`, file path, hash, timestamps and clinical payload.
- Patient Companion document sharing already has an explicit allow-list model, revocation, tenant/patient checks, and active-document checks. PC-06 invoice retrieval must reuse these semantics instead of creating a new invoice store.

### Payment truth
- `Payment` is the real cash-receipt table.
- It can reference either an `Acte` or an `Installment`; current cabinet API rejects a payment targeting both.
- `accounting_service._visible_payment_filter()` is the current visibility rule used by Accounting KPIs and patient payment listing to hide generated/voided/trashed financial effects without deleting historical rows.
- PC-06 payment history must reuse this visibility rule.

### Installment truth
- `InstallmentPlan` is the canonical payment schedule container.
- `Installment` is the canonical due item with amount, due date, paid date and status.
- Plans can reference an `Acte` through `acte_id`.
- Treasury must suppress pending installments whose linked Acte is trashed. PR #644 additionally hardens this behavior across trash/restore.

### Existing finance endpoints
- `POST /accounting/payments`: authoritative staff-side payment creation with patient ownership validation and Acte/Installment ownership checks.
- `GET /accounting/payments/patient/{patient_id}`: active payment history using `_visible_payment_filter()`.
- `GET /accounting/actes-billing/patient/{patient_id}`: active billed Actes + paid totals + remaining due.
- `GET /accounting/honoraires`: cabinet accounting projection for fee notes / Actes.
- `GET /accounting/treasury-hub`: cabinet treasury projection including installments.
- `POST /accounting/encaisser/{item_id}`: staff-side capture path; creates a `Payment` and updates related payment status.
- `PATCH /accounting/item/{item_id}`: direct edits are blocked when the item comes from a Note d'honoraires and must instead be changed through patient history for atomic reconciliation.

## Existing endpoint explicitly rejected for PC-06
`GET /patients/{patient_id}/financial-snapshot` is not a safe PC-06 truth boundary in its current form:
- `total_billed` sums all Actes without filtering `deleted_at`;
- `total_collected` sums all Payments without `_visible_payment_filter()`;
- overdue Actes do not filter `deleted_at`;
- upcoming installments do not exclude plans linked to trashed Actes;
- recent payments and payment-method aggregates include hidden/voided/trashed generated payment effects.

Decision: PC-06 MUST NOT reuse this snapshot endpoint.

## Reconciliation audit carried forward
The cross-surface honoraires audit found:
- modification propagation is already intended to remain atomic through the patient-history path;
- deletion had three defects: multi-act Notes could trash only one derived Acte, pending installments remained visible, and frontend debt cache could remain stale;
- PR #644 addresses parent-document trash, generated-payment visibility, installment suppression/restoration and frontend debt invalidation;
- `created_at` on the archive remains archive creation time; accounting uses the business date from the document payload for editable date filtering.

PC-06 must not reimplement these rules. It should project only active/canonical rows and remain compatible with the reconciliation branch when integrated.

## Online payment provider audit
No repository-backed evidence inspected here establishes an active Stripe, CMI, Payzone, PayPal or other patient online-payment gateway.
There is a generic `QRCodeType.PAYMENT` enum, but that is not a provider integration or durable payment ACK path.

Decision:
- do not expose a live online-pay action yet;
- do not create simulated provider transactions;
- do not mark anything paid from a browser redirect or optimistic client state;
- provider integration is a separate financial/security gate requiring explicit provider selection and idempotent durable confirmation.

## PC-06 minimal architecture

### Read projection
Create a dedicated Patient Companion finance projection service that:
1. receives only an already-authorized `PatientCompanionAccess`;
2. queries active Actes for that exact tenant+patient;
3. queries visible Payments using `_visible_payment_filter()`;
4. queries InstallmentPlans/Installments for that exact patient and suppresses schedules tied to trashed Actes;
5. queries active latest Note d'honoraires documents for invoice metadata;
6. derives totals from these authoritative rows at request time;
7. returns no duplicated persistent finance state.

### Invoice retrieval
Use the existing Patient Companion share/revocation/document permission boundary.
A finance invoice may be listed only if:
- Note d'honoraires is active/latest;
- it belongs to the exact authorized patient/tenant;
- an active document share grant exists for that exact document;
- download uses the existing protected document/blob path.

### Payment history
Read-only in PC-06 V1 until an online provider is selected.
Do not allow Patient Companion to mutate `Payment` directly.

### Payment schedules
Read-only projection of existing `InstallmentPlan` / `Installment`.
No second schedule table.

## Locked Goal / Success / Proof

### Goal
Expose Patient Companion finance as a read-through projection of cabinet financial truth, with invoice retrieval through existing share permissions, while keeping online payment fail-closed until a real provider with durable confirmation exists.

### Success
- exact tenant + patient isolation on every query;
- totals reconcile with active Actes and visible Payments;
- hidden/trashed/voided financial effects do not appear;
- schedules disappear when their linked accounting source is trashed;
- invoice list reflects only active/latest shared Notes d'honoraires;
- no finance persistence added for read projections;
- no optimistic paid/refunded state;
- online payment action absent until provider gate is satisfied;
- responsive/accessibility evidence on 360x800 and 390x844 Chromium + WebKit.

### Proof
- backend projection contract tests;
- cross-tenant / cross-patient isolation tests;
- reconciliation tests against accounting visibility rules;
- invoice share/revocation tests;
- installment trash-visibility tests;
- frontend truth-boundary tests;
- BEFORE -> target -> AFTER on identical viewports;
- exact-head CI;
- double check + adversarial triple check;
- explicit human visual approval before closeout/merge.

## Dependency / risk
PR #644 is concurrent reconciliation work and currently diverges from PC-06 base. PC-06 should avoid duplicating it. Before closeout, verify its merged equivalent is present in master or rebase the exact required reconciliation behavior into the then-current base.

## Next exact
Implement the read-only Patient Companion finance projection + tests first. Keep online payment fail-closed. Then add the patient UI and visual certification. Provider selection is the later human financial gate.
