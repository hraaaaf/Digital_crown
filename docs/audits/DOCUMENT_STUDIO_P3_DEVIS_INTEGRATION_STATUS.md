# Document Studio P3 — Devis Integration Status

Date: 2026-08-16
Branch: `agent/p3d-devis-phases-learning`
Current verified head before this documentation-only commit: `e8320b30987cb4088af7e0ec1fcb1902c1a21d70`

## Scope integrated

This branch carries the implementation work for P3-A through P3-G that can be verified statically without a runnable CI/runtime environment.

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

## Validation evidence available
- Targeted code diffs inspected after every large-file replacement.
- Dedicated frontend/backend unit tests committed for new policies/contracts.
- P3-F was integrated into this branch via exact verified Git blobs and a fast-forward commit.
- Transient frontend RDV guard and test were removed after the lifecycle rule was centralized in the backend.

## Current CI blocker
- Current-head CI run checked once: **31922731006** (run #385).
- Result: `failure`, but all three jobs (`Frontend (tests & build)`, `Garde production (négatif)`, `Tests & durcissement`) returned `steps: null`.
- Therefore no backend test, frontend test or build actually started.
- This is consistent with the previously identified GitHub Billing/spending-limit runner-allocation blocker; it is not evidence of a code test failure.

## Not certified / still required for P3-H
- No runnable CI result exists on the integrated head.
- No authenticated runtime/PDF visual regression has been executed on this integrated head.
- No production-readiness claim is made.

## Remaining closeout gates
1. CI must allocate a runner and execute backend/frontend tests on the integrated head.
2. Runtime Devis smoke: create/edit/reorder adult + pediatric quote, preview, explicit archive, duplicate handling, print.
3. PDF visual fixtures: short, long-label, multipage, signature, adult/pediatric teeth.
4. Responsive inspection at 390 / 768 / desktop widths.
5. Final reconciliation/merge and canonical roadmap/session closeout only after the above pass.
