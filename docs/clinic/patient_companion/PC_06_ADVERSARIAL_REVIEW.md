# PC-06 — Patient Finance — Adversarial Review

Status: MACHINE GATES PASSED — HUMAN VISUAL GATE OPEN
Branch: feature/patient-companion-pc06-finance
Reviewed product head: ded90193ce5cd65484f56b5dbb4bba1388e701fa
PR: #645 (DRAFT)
Deployment: none

## Review question
Can Patient Companion expose finance without creating a parallel ledger, leaking another tenant/patient, showing stale deleted financial rows, or claiming a payment state that the cabinet has not durably confirmed?

## Findings

### 1. Source of truth
PASS.
- billed projection reads active, accounted `Acte` rows;
- legacy standalone active/latest/accounted Notes d'honoraires are added only when no linked Acte exists;
- payments reuse `accounting_service._visible_payment_filter()`;
- installments reuse existing `InstallmentPlan/Installment`;
- no PC-06 finance persistence/table exists.

### 2. Tenant + patient isolation
PASS.
- exact active `PatientCompanionAccess` is resolved;
- service requires exact `employer_id` + `patient_id`;
- forged tenant mismatch is covered by automated test.

### 3. Deleted / hidden rows
PASS with upstream reconciliation integrated.
- deleted Actes are excluded;
- generated payments hidden by accounting visibility rules are excluded;
- installment plans linked to deleted Actes are excluded;
- PR #644 was merged to master as `70c3dea8fc30b4babe54fe230cfd902f822cf2a7`;
- PC-06 was rebuilt on that master and verified ahead 1 / behind 0 before final harness hardening.

### 4. Invoice retrieval
PASS.
- only active/latest NOTE_HONORAIRES with active exact Patient Companion share can be listed/resolved;
- revoke hides the invoice;
- download requires Patient Companion Bearer auth;
- download response is `Cache-Control: no-store`;
- no public URL is emitted;
- stale document-level payment status is not exposed.

### 5. Online payment
FAIL-CLOSED by design.
- no verified provider integration exists in repo;
- no payment CTA is exposed;
- no optimistic PAID/REFUNDED state exists.
Online payment is deferred to a dedicated future provider/security lot.

### 6. Offline behavior
PASS.
- finance is live-only;
- values are cleared before refresh;
- failed refresh does not retain old amounts as current truth;
- explicit cabinet-offline state disables finance even after a prior successful sync.

### 7. UI / visual
PASS on automated + manual inspection.
Viewports:
- Chromium 360x800;
- Chromium 390x844;
- WebKit 360x800;
- WebKit 390x844.

Observed:
- no horizontal overflow;
- download action = 44px minimum;
- no online payment CTA;
- 3 summary totals remain on one visual line on all four captures;
- Chromium/WebKit layout coherent;
- no overlap/cropping in finance section.

A first green AFTER artifact had exposed a wrapped-MAD defect. The defect was fixed and the harness was hardened using `Range.getClientRects()` so wrapped summary totals now fail certification.

## Exact-head proof — ded90193...
- PC-06 Patient Finance Certification: run `35577425192` — SUCCESS
- PC-06 BEFORE Visual Evidence: run `35577425233` — SUCCESS
- PC-06 AFTER Visual Evidence: run `35577425151` — SUCCESS
- CI: run `35577425226` — SUCCESS
- T2 Runtime Browser Certification: run `35577425300` — SUCCESS
- Patient P7 Final Certification: run `35577425258` — SUCCESS
- Patient Companion Remote Transport Gate: run `35577425256` — SUCCESS
- AFTER artifact: `10628975176`
- AFTER digest: `sha256:d86bb4752d6de762cd3f156684f8302b9a7ce3b814cfdde6865815d614758dec`
- BEFORE artifact: `10627698972`
- BEFORE digest: `sha256:4821cf8294d963b15cd126b602911e8d7197f68d9d9d22e1d80414504dba7549`

## Visual assessment
Conservative visual score: 9.2 / 10.

Strengths:
- compact mobile presentation;
- cabinet source is explicit;
- financial hierarchy is immediately readable;
- no misleading transaction action;
- corrected totals are stable on narrow widths.

Residual polish only:
- dense information and small secondary typography are acceptable but not premium enough to justify 9.5+.

## Remaining gate
Human visual approval only.

No merge and no Vercel deployment before that gate.
