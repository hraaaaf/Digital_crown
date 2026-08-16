# Document Studio P5 — Suivi Paiement Audit

Date: 2026-08-16
Branch: `agent/p5-suivi-paiement-audit`
Base: P4 Note Honoraires head `51333f7ead38259b398308ba23b680a6d7f6bac4`

## Current verdict

**P5 core financial engineering is locally converged for the findings below.**

**Full React/Vite/authenticated/browser certification is not executed and not claimed.**

---

## Initial findings and remediation

### P0-1 — installment-plan creation contract was permissive — ✅ REMEDIATED

Historical direct creation accepted a plan without an exact contract ensuring:
- positive/finite/bounded total;
- positive/finite/bounded installment amounts;
- real labels;
- at least one installment;
- exact sum of installments = plan total;
- new installments start only as `EN_ATTENTE` with no client-supplied `paid_date`.

Correction in `backend/schemas/installments.py`:
- total and installment amount bounds `> 0` and `<= 1_000_000`;
- finite amount validation;
- non-empty title/labels;
- new status constrained to `EN_ATTENTE`;
- `paid_date` forbidden on creation;
- exact cent reconciliation through `validate_installments()`.

Evidence: creation contract tests included in consolidated backend **15/15 PASS**.

---

### P0-2 — existing plan could look paid in UI without a backend payment — ✅ REMEDIATED

Historical `InstallmentStudio` loaded the latest persisted plan into local editable state. The `Réglé` checkbox only changed local React state and could visually present an installment as paid while no backend `Payment` existed.

Correction:
- persisted plans moved to `InstallmentTrackingPanel`;
- statuses are read from backend only;
- no local unpay/pay checkbox;
- `Enregistrer règlement` opens an explicit confirmation dialog and calls `PUT /installments/{id}` with `status=PAYE` + explicit method;
- UI reloads the plan only after backend success;
- the dialog states that a real accounting Payment is created and a dedicated counter-entry would be required to undo it.

No success state is inferred before the backend responds.

---

### P0-3 — installment update could break plan reconciliation — ✅ REMEDIATED

Historical `InstallmentUpdate` allowed arbitrary statuses and loosely bounded amounts. A pending installment amount could be edited without proving the resulting plan still matched its contractual total.

Correction:
- update amount must remain positive/finite/bounded;
- update status constrained to `EN_ATTENTE | PAYE`;
- client cannot inject `paid_date`;
- payment method is legal only with an explicit PAYE transition payload;
- `validate_updated_installment_amounts()` recomputes all plan amounts with the proposed value and requires exact reconciliation;
- paid installment cannot be reopened or rechiffré without a dedicated counter-entry workflow.

Evidence included in consolidated backend **15/15 PASS**.

---

### P0-4 — deleting a paid plan could destroy payment linkage — ✅ REMEDIATED

DB relationship audit showed:
- deleting `InstallmentPlan` cascades its installments;
- linked `Payment.installment_id` uses `SET NULL`.

Therefore deleting a plan containing real collection history could leave Payment rows while erasing their installment linkage.

Correction:
- `ensure_installment_plan_deletable()` rejects deletion when any installment is `PAYE` or any linked Payment exists;
- only a fully unpaid plan with no linked payment history can be deleted.

Evidence included in consolidated backend **15/15 PASS**.

---

### P1-1 — global Studio “Enregistrer” did not persist a P5 plan — ✅ REMEDIATED

Historical `useDocumentGenerator` always routes `activeTab=echeancier` through `/installments/generate-preview`, including when the global footer passed `archive=true`. The footer could therefore display `Enregistrer` while creating no plan.

Correction:
- global archive/save action is hidden for P5 in `StudioFooter`;
- P5 has an explicit `Enregistrer le nouveau plan` action inside its own creator;
- that action posts to `POST /installments/` and reloads backend tracking after success;
- global `Aperçu` / `Imprimer` remain document-preview actions only.

The persistence boundary is now explicit.

---

### P1-2 — creator and tracking were conflated — ✅ REMEDIATED

Historical page copied the latest existing plan into the same editable local form used to build a new plan.

Correction separates surfaces:
- **Suivi des paiements** = backend-authoritative persisted plans, read/reload/pay/remind;
- **Nouveau plan de paiement** = local draft only, all rows initially pending;
- successful save resets the draft and refreshes tracking.

A persisted plan is no longer silently transformed into a local draft.

---

### P1-3 — no authoritative paid/remaining/next-due summary — ✅ REMEDIATED

Added pure `InstallmentTrackingPolicy` using cent arithmetic and backend statuses to compute:
- paid total;
- remaining total clamped >= 0;
- paid/pending counts;
- earliest pending due date;
- overdue count.

Evidence: **4/4 PASS** local execution.

---

### P1-4 — TPE alias could diverge from backend enum mapping — ✅ REMEDIATED

The explicit payment route now maps:
- `ESPECES` → `PaymentMethod.ESPECES`;
- `CARTE` / `TPE` → `PaymentMethod.CARTE`;
- `CHEQUE` → `PaymentMethod.CHEQUE`;
- `VIREMENT` → `PaymentMethod.VIREMENT`.

This avoids enum-name inference for the TPE UI alias.

---

### P1-5 — new-plan save payload was rebuilt inline in React — ✅ REMEDIATED

Added `InstallmentPlanDraftPolicy` as the single frontend save-payload contract:
- real patient id;
- trimmed title;
- positive finite amounts;
- at least one installment;
- strict ISO date shape;
- exact cent reconciliation;
- every new row forced to `EN_ATTENTE`;
- canonical API date payload.

`InstallmentStudio` uses the same policy both to enable the save action and to build the posted payload.

Evidence: production policy `tsc --strict` PASS + **8/8 assertions PASS** under local Linux.

---

## Tracking / reminder scope

P5 now exposes a manual WhatsApp reminder action for unpaid installments. It opens WhatsApp with a prefilled message built from authoritative backend installment data.

This is **not** a scheduled/server-side reminder system and is not described as one.

---

## Preview semantics

`POST /installments/generate-preview` was inspected and remains read-only: it renders a PDF and does not persist a plan, installment or payment.

Preview remains separate from the explicit save action.

---

## Current P5 UX

### Existing persisted plans
- backend reload;
- total contractuel;
- payé;
- restant;
- prochaine échéance;
- nombre en retard;
- per-installment backend status;
- manual WhatsApp reminder;
- explicit real payment with method + confirmation;
- no direct unpay action.

### New plan draft
- title / total;
- exact advance + monthly allocation;
- manual rows;
- exact planned-total warning;
- explicit save to backend;
- all new rows pending;
- no fake paid checkbox.

---

## Execution evidence

- backend creation/update/delete integrity suite: **15/15 PASS** local Linux;
- tracking summary policy: **4/4 PASS**;
- create-payload policy: **`tsc --strict` PASS + 8/8 assertions PASS**;
- preview code path: statically verified read-only;
- InstallmentStudio fake local paid/edit flow removed: diff verified;
- P5 global misleading save action removed: diff verified.

Not executed:
- real React/Vite full build;
- authenticated API/UI smoke;
- real Payment row inspection after a browser-triggered installment payment;
- browser 390 / 768 / desktop;
- keyboard focus trap / Escape behavior for payment dialog;
- real WhatsApp handoff on target devices.

---

## Deferred product gap — atomic restructuring of an existing plan

P5 deliberately does not expose arbitrary amount edits on an existing persisted plan. The backend requires every mutation to preserve exact reconciliation, and sequential single-row amount edits cannot safely implement a two-row rebalance.

If product later requires restructuring a persisted unpaid plan, implement a dedicated **atomic plan-reallocation endpoint** that validates all replacement amounts together. Do not emulate this with multiple sequential installment updates.

This is classified as a product enhancement, not an integrity defect.

---

## P5 roadmap status

1. **P5-A — creation contract** — ✅ local PASS.
2. **P5-B — update/delete traceability** — ✅ local PASS.
3. **P5-C — backend-authoritative tracking** — ✅ code/policy local PASS.
4. **P5-D — explicit payment UX** — ✅ code path integrated; authenticated runtime pending.
5. **P5-E — new-plan persistence boundary** — ✅ code/policy local PASS.
6. **P5-F — reminder + summaries** — ✅ manual reminder + deterministic summary; device/runtime pending.
7. **P5-G — responsive/accessibility/browser** — ⏳ runtime/browser pending.
8. **P5-H — final recertification/merge** — ⏳ pending full-app gates.

## Exact deferred gate

To fully certify P5 later:
1. complete checkout + real frontend dependencies;
2. full frontend tests/build;
3. authenticated create plan → reload → pay by each method → verify Payment row + installment status → reopen patient;
4. verify deletion guard on paid history;
5. preview/print remains read-only;
6. browser 390 / 768 / desktop + keyboard/touch/dialog behavior;
7. only after PASS: ready review → merge stack → post-merge canonical closeout.

## Progress rule

No artificial weighting exists. Global P5 completion percentage remains **indeterminate**.
