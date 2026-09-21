# PC-06 — Patient Finance — Adversarial Review

Status: INTERNAL REVIEW COMPLETE; EXTERNAL / CI / VISUAL GATES OPEN
Reviewed branch: feature/patient-companion-pc06-finance
Reviewed through: cc7073e38505837f1fad04d3455dfd378b0ce58c
PR: #645 (DRAFT)
Deployment: none

## Review question
Can Patient Companion expose finance without creating a parallel ledger, leaking another tenant/patient, showing stale deleted financial rows, or claiming a payment state that the cabinet has not durably confirmed?

## Findings

### 1. Source of truth
PASS by code inspection.
- billed projection reads active, accounted `Acte` rows;
- legacy standalone active/latest/accounted Notes d'honoraires are added only when no linked Acte exists;
- payments reuse `accounting_service._visible_payment_filter()`;
- installments reuse existing `InstallmentPlan/Installment`;
- no PC-06 finance persistence/table exists.

### 2. Tenant + patient isolation
PASS by code inspection; automated proof pending CI.
- route resolves the exact active `PatientCompanionAccess`;
- service joins Patient and requires exact `employer_id` + `patient_id`;
- a forged tenant mismatch test returns an empty projection.

### 3. Deleted / hidden rows
PARTIAL PASS.
- deleted Actes are excluded;
- generated payments hidden by the accounting visibility filter are excluded;
- installment plans linked to deleted Actes are excluded.
Residual dependency: PR #644 fixes the cabinet-side parent Note d'honoraires trash/reconciliation flow. Until its equivalent is in master, an inconsistent upstream trash operation can still leave the source document/other child rows active. PC-06 must not guess the user's deletion intent.

### 4. Invoice retrieval
PASS by code inspection; automated proof pending CI.
- only active/latest NOTE_HONORAIRES with an active exact Patient Companion document share can be listed/resolved;
- revoke hides the invoice;
- download requires Patient Companion auth and returns no-store;
- no public download URL is emitted.
Hardening applied during review: stale document-level `payment_status` was removed from the patient invoice payload.

### 5. Online payment
FAIL-CLOSED by design.
- no verified provider integration was found;
- no payment CTA is exposed;
- no browser redirect can mutate financial state;
- no optimistic PAID/REFUNDED state exists.
Human financial/security gate remains: provider selection + durable idempotent confirmation contract.

### 6. Offline behavior
PASS by design inspection; frontend proof pending CI/visual.
- PC-06 finance is live-only;
- values are cleared before refresh;
- network failure does not retain a previous amount as current truth;
- offline UI asks for cabinet reconnection rather than presenting stale financial values.

### 7. UI safety
TARGET IMPLEMENTED; visual proof pending.
- no online-payment CTA;
- compact mobile cards rather than desktop tables;
- target requires 44px minimum actions and no horizontal overflow;
- BEFORE/AFTER workflows cover Chromium + WebKit at 360×800 and 390×844.

## Open gates
1. exact-head PC-06 backend/frontend/build CI;
2. exact-head BEFORE visual;
3. exact-head AFTER visual;
4. inspect generated visual artifacts and score conservatively;
5. PR #644/equivalent merged into master, then rebase/re-verify PC-06;
6. human visual approval;
7. online payment provider decision if online payment remains in PC-06 scope.

## Retained assessment
No numeric certification score yet. The implementation is not certifiable while exact-head CI/visual evidence and the upstream reconciliation dependency are unresolved.

## Next exact
Use CI results when available. Correct any failures. Inspect visual evidence. Then rebase on the master that contains the honoraires reconciliation fix and rerun exact-head certification before any closeout/merge.
