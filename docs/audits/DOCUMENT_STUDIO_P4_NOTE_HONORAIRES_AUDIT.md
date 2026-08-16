# Document Studio P4 — Note Honoraires Audit

Date: 2026-08-16
Branch: `agent/p4-note-honoraires-audit`
Base: P3 closeout branch `agent/p3d-devis-phases-learning` at `603c5a7e5d7a909e8a32a31cd75fa4f8f52e32c5`

## Status of proof

- **CODE VÉRIFIÉ**: yes, for the findings below.
- **TESTS EXÉCUTÉS P4**: not yet for the new findings in this audit baseline.
- **INTERACTION RUNTIME**: not executed.
- **CERTIFICATION FINANCIÈRE / PRODUCTION**: not claimed.

Historical shared engineering remains relevant from `DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`, notably:
- PARTIEL fail-closed;
- exact installment reconciliation for global Honoraires;
- exact PAYE allocation per Acte;
- shared catalog/odontogram/accounting policies.

This P4 audit is intentionally based on the current stacked P3 closeout branch because P3 changed shared accounting and DocumentHub code.

---

## P0-1 — Honoraires backend contract is permissive enough to persist invalid financial lines

### Verified code path

`HonorairesData` currently uses a permissive `PaymentItem`:
- empty `acte` allowed;
- `montant` has no lower/upper bound;
- structured `dents` has no FDI validation or canonicalization;
- `payments` may be empty;
- `teeth_data` has no consistency check against real payment lines.

`DocumentRequest.data` is a generic dict. On archive, `persist_honoraires_lines()` reads the raw items and:
- substitutes blank acts with the generic label `Acte`;
- casts `montant` to float without enforcing non-negative/bounded billing;
- creates an `Acte` for every supplied line;
- when status is PAYE, skips the linked `Payment` for amounts `<= 0`, which can leave an invalid billed Acte without matching collection.

### Risk

A direct or malformed API client can bypass frontend validation and create financially inconsistent Acte rows.

### Required correction

Fail closed in the backend schema/service before any archive/accounting write:
- real non-empty act required;
- finite amount `0 <= montant <= 1_000_000`;
- adult/pediatric FDI validation + canonical structured dent label;
- at least one real Honoraires line;
- `teeth_data` consistency where present;
- phase/presentation rows never persist as billable acts;
- payment method validation only when a real collection is being recorded.

**Priority: P0.**

---

## P0-2 — stale installment plan can contaminate a new unique Honoraires PDF/archive

### Verified code path

`DocumentHub` automatically fetches the latest patient installment plan on patient load and stores its installments in the shared accounting store.

`useDocumentGenerator.buildPayload()` sends `installments` in every Honoraires payload, regardless of `isGlobalNote`.

`AccountingGenerator.generate_note()` renders an installment table whenever `data.installments` is non-empty; it does not require global-note semantics before showing `SUIVI DES RÈGLEMENTS`.

The raw request data is also archived as clinical data, so stale installments can be preserved with the new document even when no new plan is intended.

### Risk

A previous patient's payment schedule can appear on a new Note Honoraires configured as `Unique`, producing an inaccurate financial document.

### Required correction

- Only include installments in the Honoraires document payload when `isGlobalNote === true`.
- Rendering must independently fail closed: no installment table unless the document is explicitly global/planned.
- Do not reuse a previously persisted plan as draft input for a new Note Honoraires unless the user explicitly chooses to import it.

**Priority: P0.**

---

## P1-1 — pending Honoraires can display a payment method as if collection occurred

### Verified code path

The accounting store defaults to:
- `paymentStatus = EN_ATTENTE`;
- `paymentMode = Espèces`.

Every Honoraires line payload carries `mode_reglement`, even when status is `EN_ATTENTE`.

The PDF table always renders a `PAIEMENT` column from `mode_reglement`; it does not receive/display the document-level `payment_status` in a way that distinguishes unpaid from collected.

### Risk

A non-collected Note Honoraires can visually state `Espèces`, which is misleading financial semantics.

### Required correction

Separate billing status from collection method:
- pending line/document: display `EN ATTENTE` / no collection method;
- paid: display normalized collection method;
- never infer cash from a default when no payment occurred.

**Priority: P1.**

---

## P1-2 — global/planned flag is not part of `HonorairesData` used by the PDF generator

### Verified code path

Frontend sends `is_global_note` in the raw Honoraires data.

Backend persistence reads the raw request dict and can create a payment plan from it.

But `HonorairesData` does not declare `is_global_note`. Under the current Pydantic behavior, the extra field is ignored when constructing `HonorairesData`; therefore `generate_note()` sees `getattr(data, 'is_global_note', False)` as false.

### Risk

A planned/global Honoraires flow can create installment persistence while the PDF title remains ordinary `NOTE D'HONORAIRES` instead of the intended global/planned variant.

### Required correction

Declare and validate global-note semantics in the typed Honoraires payload used by both persistence and PDF rendering.

**Priority: P1.**

---

## P1-3 — archived Honoraires reopen drops odontogram metadata

### Verified code path

Devis reopening uses `hydrateArchivedDevisRows(items, teeth_data)`.

Honoraires reopening maps raw `payments` only and restores:
- description;
- dent;
- price;
- toothNumbers.

It does not rehydrate:
- odontogram treatment key/code;
- surfaces;
- notes.

### Risk

Round-trip is lossy and subsequent edit/rearchive can silently discard structured clinical metadata.

### Required correction

Introduce an Honoraires archive hydration path equivalent in integrity to Devis, without inventing financial rows.

**Priority: P1.**

---

## P1-4 — Honoraires PDF still uses uniform shrinking down to 2 pt

### Verified code path

`generate_note()` computes one `min_fs` across all act/dent/payment/amount cells using `get_adaptive_style(..., min_fs=2.0)`, then applies that smallest font uniformly to the whole table.

This is the exact class of readability defect already removed from Devis P3-F.

### Risk

A long Honoraires line can shrink the full financial table below the central readable floor.

### Required correction

Adopt the Devis P3-F strategy:
- central readable floor >= 7 pt;
- wrapping for long act labels;
- adaptive narrow cells without uniform whole-table shrink;
- multipage header repeat where needed.

**Priority: P1.**

---

## P1-5 — `Confirmer l'Encaissement` does not perform an encaissement

### Verified code path

In the Honoraires treasury modal, `Confirmer l'Encaissement` only executes `setIsTreasuryModalOpen(false)`.

No financial write happens at this button. Persistence occurs later only when the document generation/archive flow runs.

### Risk

The UI claims a financial action that has not happened yet. A user may reasonably believe cash/card/cheque collection has been recorded after clicking it.

### Required correction

Either:
- rename the action to accurately describe configuration, e.g. `Appliquer les paramètres de règlement`; or
- make it the explicit transactional save action with clear success/failure semantics.

Recommendation: keep document archive as the single transaction boundary and **rename the modal/action**, avoiding a second write path.

**Priority: P1.**

---

## Historical strengths retained

The following prior fixes remain valuable and must not regress:
- `PARTIEL` refused unless a real collected amount is supplied through the dedicated payment flow;
- unknown payment methods fail closed in actual payment persistence;
- global installment totals reconcile exactly before DB write;
- `PAYE` creates one exact linked Payment per Acte instead of a global orphan payment;
- fresh-PDF print protection;
- accounting dirty-state protections;
- catalog-authoritative pricing and shared deterministic totals.

---

## P4 correction order

1. **P4-A — Honoraires backend financial contract** — P0.
2. **P4-B — installment isolation / global-note typed contract** — P0.
3. **P4-C — payment status vs collection method semantics** — P1.
4. **P4-D — archive/reopen structured metadata round-trip** — P1.
5. **P4-E — professional PDF readability** — P1.
6. **P4-F — treasury modal semantics + post-archive UX** — P1.
7. **P4-G — responsive/accessibility/runtime smoke**.
8. **P4-H — final recertification/closeout**.

## Progress rule

No artificial weighting is assigned. P4 global completion percentage remains **indeterminate** until a validated weighting/criterion model is adopted.
