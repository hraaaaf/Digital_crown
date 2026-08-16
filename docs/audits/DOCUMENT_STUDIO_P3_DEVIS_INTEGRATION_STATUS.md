# Document Studio P3 — Devis Integration Status

Date: 2026-08-16
Branch: `agent/p3d-devis-phases-learning`
Current functional head verified before this documentation-only commit: `c7385e2affdcfcef049c524f18f71138925c102a`

## Scope integrated

This branch carries the implementation work for P3-A through P3-G. P3-H now has both static inspection evidence and targeted local execution evidence, but the full integrated application is not certified yet.

### P3-A — financial isolation / backend contract
- Devis payload excludes installments and global-note semantics.
- Backend rejects non-empty Devis installments.
- Devis requires at least one real item after phase-row sanitization.
- Empty acts, negative/excessive amounts, and invalid adult/pediatric FDI numbers are rejected.
- Structured `dents` becomes canonical over free-text `dent`.
- Devis generation no longer archives implicitly; archive must be requested.

### P3-B — odontogram source of truth
- Accounting rows are the canonical tooth/document source.
- PDF `dent/dents/teeth_data` derives from canonical accounting rows.
- Odontogram metadata persists on quote rows.
- Multi-tooth labels are normalized to the same comma-separated representation as backend/PDF (`14, 15, 16`).

### P3-C — catalog pricing / dentition modes
- Managed catalog price is authoritative for catalog selections.
- Missing catalog price fails closed to unresolved/zero rather than stale remembered price.
- Adult and pediatric odontograms have separate valid quick groups.
- Pediatric teeth are accepted by the treatment selector.
- Named/global/group shortcuts are repriced through the managed catalog.

### P3-D — phases / bundles / learning
- Phase separators are presentation-only and stripped before Devis validation/PDF.
- Phase rows are non-financial in validation, totals, payload and UI editing.
- Duplicate DocumentHub bundle engine removed; AccountingStudio is the single visible Devis bundle surface.
- Bundle prices resolve through the managed catalog; unresolved amounts remain explicit.
- Frontend `/accounting/record-act` duplicate writes removed.
- `PriceBrain.recordAct` keeps `usageCount` unchanged and is only a local price memory.
- Financial act learning occurs only after real archive.

### P3-E — connections / lifecycle
- Treatment-plan result can explicitly create a neutral Devis.
- Plan conversion does not invent prices.
- Manual lines can be moved up/down.
- Document total uses one phase-aware policy.
- Printing is armed only after a fresh PDF is returned, preventing stale-preview printing after conflicts.
- Generic financial-document RDV suggestion with hard-coded 4-week interval removed.

### P3-F — professional PDF
- Long act labels wrap instead of forcing a 2 pt uniform font.
- Central readable typography floor is enforced (>= 7 pt).
- Devis table headers repeat across pages.
- Closure text can wrap without all-NBSP shrinking.

### P3-G — UX / responsive / accessibility
- Row move/delete controls are visible on touch-sized layouts.
- Direct odontogram tooth selection supports keyboard Enter/Space, labels, pressed state and focus indication.
- Preview becomes full-overlay below XL and fixed 550 px side pane on XL desktop.

## Executed P3-H evidence

The GitHub runner remains unavailable, so targeted tests were reconstructed locally from the exact connected GitHub source at the functional head. These are real executions of the relevant source modules, but not a clone/run of the complete application.

### Backend targeted execution
- Exact P3 lifecycle, phase sanitizer, installment reconciliation and Devis schema contracts were materialized with their committed P3 tests.
- `pytest`: **13 passed**, 1 unrelated existing Pydantic class-based Config deprecation warning.
- Covered: explicit Devis archive, archive-only learning, no generic financial RDV, phase sanitization, non-empty-installment rejection, amount limits, FDI validation, canonical structured teeth and backward-compatible empty installment list.

### Frontend pure-policy execution
- Exact pure TypeScript policy modules compiled with `tsc --strict`.
- Committed behavioral assertions were replayed in Node because Vitest is not installed in the local execution image.
- Pricing/bundles/order/total/plan-conversion/learning policies: **22/22 assertion groups passed**.
- Odontogram source/mode/metadata policies after UI/PDF label alignment: **9/9 assertion groups passed**.
- `PriceBrain` local-memory behavior: **1/1 passed**; repeated price edits leave `usageCount` at 0.

### P3-F isolated rendering execution
- The actual P3-F `generate_devis` core algorithm was exercised in a controlled ReportLab harness with the same readability policy and minimal generator stubs.
- A5 fixture with 36 long treatment lines rendered successfully to **3 pages**.
- Table header detected on **3/3 pages**.
- Minimum observed paragraph font size: **7.5 pt**.
- Minimum requested adaptive floor: **7.0 pt**.
- Long labels and `TOTAL GÉNÉRAL` were present in extracted PDF text.
- This proves the targeted multipage/readability behavior, not the complete cabinet-branded PDF runtime.

## Current GitHub CI blocker
- Current functional-head CI run checked once: **31923178969** (run #395), head `c7385e2affdcfcef049c524f18f71138925c102a`.
- Result: `failure`, but all three jobs (`Frontend (tests & build)`, `Garde production (négatif)`, `Tests & durcissement`) returned `steps: null`.
- Therefore no GitHub-hosted backend test, frontend test or build actually started.
- This remains consistent with the previously identified GitHub Billing/spending-limit runner-allocation blocker; it is not evidence of a code test failure.

## Not certified / still required for P3-H
- No full-repository CI/build has executed on the integrated branch.
- No authenticated full-app Devis runtime smoke has been executed on this integrated branch.
- React/jsdom dependencies are not available in the local isolated execution image, so an honest integrated UI/browser smoke cannot be substituted with a synthetic mock.
- No production-readiness claim is made.

## Remaining closeout gates
1. GitHub CI (or an equivalent full-repository environment) must execute the complete backend/frontend suite and build.
2. Authenticated runtime Devis smoke: create/edit/reorder adult + pediatric quote, preview, explicit archive, duplicate handling and print.
3. Cabinet-branded PDF visual fixtures still required for short document, signature and adult/pediatric clinical examples; long-label/multipage behavior already has isolated execution evidence.
4. Real responsive inspection at 390 / 768 / desktop widths.
5. Final merge and canonical ROADMAP/SESSION closeout only after the remaining integrated gates pass.
