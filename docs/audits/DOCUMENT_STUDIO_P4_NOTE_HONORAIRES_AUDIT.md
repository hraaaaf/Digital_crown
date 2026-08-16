# Document Studio P4 — Note Honoraires Audit

Date: 2026-08-16
Branch: `agent/p4-note-honoraires-audit`
Base: P3 closeout branch `agent/p3d-devis-phases-learning` at `603c5a7e5d7a909e8a32a31cd75fa4f8f52e32c5`
PR: `#90` (stacked, draft)

## Current verdict

**P4-A → P4-F: engineering remediated with targeted local execution evidence.**

**P4-G: static accessibility/responsive hardening applied; real browser/runtime smoke not executed.**

**P4-H: not certified / not merge-ready.**

No financial, production or full-app certification is inferred from isolated tests.

---

## Initial findings and remediation

### P0-1 — permissive Honoraires backend contract — ✅ REMEDIATED

Historical `PaymentItem/HonorairesData` could accept blank acts, invalid/negative amounts, invalid FDI and inconsistent `teeth_data`, while `persist_honoraires_lines()` could stage Acte rows from raw request items.

Correction:
- dedicated `backend/schemas/honoraires.py` fail-closed contract;
- non-empty real act required; presentation phase rows refused;
- finite `0 <= montant <= 1_000_000`;
- adult + pediatric FDI validation, sorted/deduplicated structured teeth and canonical `dent`;
- at least one Honoraires line;
- `teeth_data` must match real tooth + act + price;
- payment methods normalized and unknown values rejected;
- strict P4 `PaymentItem`, `HonorairesData`, `DocumentRequest` re-exported last from `backend.schemas` so `/documents/generate` validates before PDF/archive.

Important transaction finding retained: `archive_document()` commits the archive before `persist_honoraires_lines()`, therefore validation **must** occur before archive. P4 now does so through the request/schema boundary.

Evidence: targeted backend contract execution **13/13 PASS** after P4-C.

---

### P0-2 — stale installment plan contaminating a new Unique note — ✅ REMEDIATED

Historical flow:
- `DocumentHub` loads the latest patient installment plan into the shared accounting store;
- Honoraires payload previously carried store installments regardless of new-note intent;
- historical PDF rendered any non-empty installment list.

Corrections:
- P4 `DocumentRequest` strips installments from every non-global Honoraires request **before inherited validators, rendering and archive**;
- typed `HonorairesData.is_global_note` added;
- Unique `HonorairesData` strips installments independently;
- Global notes preserve installments only when explicitly global and reconcile them exactly to the billed total;
- frontend `AccountingHonorairesInstallmentPolicy` clears inherited installments on the explicit `Unique → Global` transition, preventing silent reuse of the previously loaded patient plan;
- an existing in-progress global draft remains stable.

Evidence:
- backend included in **13/13 PASS**;
- frontend installment policy **4/4 PASS** locally.

---

### P1-1 — pending note displaying a collection method — ✅ REMEDIATED

Historical default `paymentStatus=EN_ATTENTE` + `paymentMode=Espèces` could cause the PDF to visually state cash even when no collection occurred.

Corrections:
- P4 request sanitizer rewrites each non-PAYE line to `mode_reglement = EN ATTENTE` before rendering/archive;
- PAYE preserves/normalizes the real collection method;
- persistence still creates `Payment` rows only for PAYE;
- payment-method controls are disabled in the P4 modal until status is `PAYE`.

Compatibility verified against persistence aliases:
- `Espèces` → `ESPECES`;
- `TPE` → `CARTE`;
- `Chèque` → `CHEQUE`;
- `Virement` → `VIREMENT`.

Evidence: included in backend **13/13 PASS**.

---

### P1-2 — `is_global_note` lost before PDF generation — ✅ REMEDIATED

Historical typed `HonorairesData` did not declare `is_global_note`, so the raw persistence flow and typed PDF model could disagree.

Correction:
- `is_global_note: bool` is now part of the strict typed P4 Honoraires model;
- safe Honoraires renderer uses that field for the global title and installment section;
- installment section renders only when the typed note is explicitly global.

Versioned PDF regression tests cover global title/section and Unique isolation.

---

### P1-3 — archive → reopen loses odontogram metadata — ✅ REMEDIATED

Historical Honoraires reopen used a raw payment mapper that lost `_odontogramKey`, treatment code, surfaces and notes.

Correction:
- `DocumentHub` now uses the existing canonical `hydrateArchivedDevisRows(srcItems, d.teeth_data)` path for both Devis and Honoraires-shaped archived rows;
- the helper already accepts `montant` as the Honoraires amount source;
- no financial row is invented.

Diff verification on commit `dedcb46a…`: only the lossy Honoraires mapping was replaced by the canonical hydration call.

Evidence: Honoraires-shaped archive hydration **1/1 PASS** locally.

---

### P1-4 — Honoraires PDF could shrink to 2 pt / multipage rebuild risk — ✅ REMEDIATED FOR P4

Two defects were verified:
1. historical `generate_note()` derived one uniform table font with `min_fs=2.0` and NBSP act labels;
2. shared historical `_build_pdf()` attempts to rebuild the same flowable list to force one page. Direct ReportLab execution proved that `SimpleDocTemplate.build(flowables)` consumes that list (`20 → 0`), so a retry could overwrite a valid multipage output with an empty/partial build.

Correction is deliberately **P4-only** so paused P3 behavior is not changed:
- new `backend/services/generators/honoraires_gen.py::HonorairesGenerator`;
- `DocumentFactory.create_note_honoraires()` uses this generator;
- Devis still uses historical `AccountingGenerator`;
- Honoraires builds **exactly once** and allows natural multipage flow;
- table `repeatRows=1`;
- normal spaces allow act wrapping;
- central readable floor >= 7 pt for table and installment values;
- no uniform 2 pt shrink;
- closure uses normal wrapping at 9.5 pt;
- installment table is rendered only for typed global notes.

Targeted Linux rendering evidence using the same P4-E table widths/adaptive algorithm:
- **36/36 long rows preserved**;
- **6 pages**;
- table header **6/6 pages**;
- `TOTAL GÉNÉRAL` present;
- `EN ATTENTE` present;
- minimum observed style **7.5 pt**;
- configured floor **7.0 pt**;
- one ReportLab build only;
- PDF size 9027 bytes.

Versioned regression file: `backend/tests/test_honoraires_pdf_safety.py`.

Caveat: the isolated Linux runtime lacks `arabic_reshaper/python-bidi` and the complete application dependency tree, so the versioned full-module PDF test has not been represented as a full-repo test execution.

---

### P1-5 — treasury modal claimed to perform collection — ✅ REMEDIATED

Historical button `Confirmer l'Encaissement` only closed the modal; the financial transaction boundary remained document archive.

Correction keeps one transaction boundary and fixes the language:
- `Procéder à l'Encaissement` → `Paramètres de règlement`;
- modal title → `Paramètres de règlement`;
- `Mode d'Encaissement` → `Mode de règlement (si réglé)`;
- `Confirmer l'Encaissement` → `Appliquer les paramètres`.

Commit `db659980…` was diff-verified: only those four strings changed.

Post-archive behavior was reviewed: successful Honoraires archive intentionally resets the draft to a blank line. This is retained as duplicate-prevention/new-document behavior, not classified as a defect.

---

## P4-G — static responsive/accessibility hardening

Applied in the financial modal:
- launcher exposes dialog state;
- modal has `role=dialog`, `aria-modal`, labelled title;
- icon-only close button has an accessible label;
- `Comptabiliser CA` uses switch semantics with `aria-checked`;
- payment status buttons expose `aria-pressed`;
- dead `PARTIEL` action removed from this modal because the store intentionally refuses partial payment here; partial collection remains a dedicated payment-flow concern;
- payment-method buttons are disabled until `PAYE` and expose pressed state;
- Unique/Global buttons expose pressed state;
- installment delete button has an accessible label;
- existing row move/delete controls remain touch-visible and labelled;
- inherited P3 preview contract remains overlay below XL / side panel on XL.

Commit `c57eed14…` was diff-verified for these accessibility/financial-control changes only.

### Still unexecuted P4-G gates
- real React mount/build;
- browser 390 / 768 / desktop;
- keyboard focus/focus trap/escape behavior of the modal;
- real touch interaction;
- authenticated patient workflow.

---

## Historical strengths retained

The following prior safeguards remain relevant and must not regress:
- `PARTIEL` is fail-closed outside its dedicated payment flow;
- global installment totals reconcile exactly before DB write;
- `PAYE` creates one exact linked Payment per Acte rather than an orphan global payment;
- fresh-PDF print protection;
- accounting dirty-state protections;
- catalog-authoritative pricing and deterministic totals;
- P3 shared odontogram metadata preservation.

---

## P4 execution evidence summary

- P4 backend financial contract/status/global semantics: **13/13 PASS** targeted local execution.
- Inherited-installment frontend policy: **4/4 PASS**.
- Honoraires archive hydration: **1/1 PASS**.
- P4-E targeted long PDF: **PASS**, 36 rows / 6 pages / header 6/6 / floor >= 7 pt.
- Four treasury copy changes: diff-verified.
- P4-G accessibility changes: diff-verified.
- Full React/Vite build: **NOT EXECUTED**.
- Authenticated runtime/browser smoke: **NOT EXECUTED**.
- Cabinet-branded/signature PDF: **NOT EXECUTED**.

---

## P4 correction roadmap status

1. **P4-A — Honoraires backend financial contract** — ✅ local targeted PASS.
2. **P4-B — installment isolation / global-note typed contract** — ✅ local targeted PASS.
3. **P4-C — payment status vs collection method semantics** — ✅ local targeted PASS.
4. **P4-D — archive/reopen structured metadata round-trip** — ✅ local targeted PASS.
5. **P4-E — professional PDF readability/integrity** — ✅ targeted rendering PASS; full cabinet renderer not yet certified.
6. **P4-F — treasury modal semantics + post-archive UX** — ✅ code/diff verified.
7. **P4-G — responsive/accessibility/runtime smoke** — 🟡 static hardening done; browser/runtime pending.
8. **P4-H — final recertification/closeout** — ⬜ pending full-app gates.

## Exact resume gate

To close P4-H without fiction:
1. complete checkout with real frontend dependencies;
2. execute real frontend tests/build;
3. authenticated Note Honoraires smoke: Unique pending, Unique PAYE for every method, Global planned, archive, reopen, duplicate, print;
4. real PDF cabinet branding/signature + short/long/global fixtures;
5. browser 390 / 768 / desktop, keyboard/touch/modal behavior;
6. only after PASS: ready review, merge stack in correct order, canonical post-merge closeout.

## Progress rule

No artificial weighting is assigned. P4 global completion percentage remains **indeterminate** until a validated weighting/criterion model is adopted.
