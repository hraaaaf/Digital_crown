# Document Studio P3 — Devis Integration Status

Date: 2026-08-16
Branch: `agent/p3d-devis-phases-learning`
Functional code head locally re-executed: `e25c01f63fbe4e1625f2b53751efedd57d9cefd9`
Full-repository certification harness: `scripts/certify_p3_devis.sh`

## Chantier status

**CLOSED / PAUSED UNTIL FURTHER NOTICE — product decision 2026-08-16.**

This is an operational closeout, **not** a claim of full-app certification or merge readiness. P3-A through P3-G are substantially hardened and P3-H has strong local Linux evidence. The remaining full authenticated React/build/browser/cabinet gates are deliberately deferred until P3 is reopened.

PR `#77` remains **open + draft** to preserve the unmerged work and exact restart point.

## Scope integrated

P3-A through P3-G are integrated on the branch, including defects found during P3-H review. P3-H has substantial **local Linux execution evidence** independent of GitHub Actions.

### P3-A — financial isolation / backend contract
- Devis excludes inherited installments/global-note semantics.
- Backend rejects non-empty Devis installments.
- At least one real item is required after phase sanitization.
- Amount limits and adult/pediatric FDI validation are enforced.
- Structured `dents` is canonical over free-text `dent`.
- Devis archive remains explicit.

### P3-B — odontogram source of truth
- Structured accounting rows are the canonical tooth/document source.
- Multi-tooth labels use the same comma-separated representation as backend/PDF.
- `teeth_data` derives from canonical `toothNumbers`, not stale `_odontogramKey` values.
- Backend rejects orphan/inconsistent tooth/act/price combinations.
- Treatment code, surfaces and notes persist on quote rows.
- Archived Devis reopening rehydrates `items + teeth_data` without inventing financial rows.
- Notes/surfaces are re-injected into `TreatmentSelector` and preserved on partial edits.
- Structured FDI lists are sorted/deduplicated before schema validation without mutating the caller row.

### P3-C — catalog pricing / dentition
- Managed catalog is authoritative for catalog acts.
- Missing catalog tariff stays unresolved/zero instead of silently using memory.
- Adult/pediatric dentition modes and quick groups are separated.
- Named/global/group/bundle prices resolve through the catalog.
- Non-authoritative fallback durations were removed.

### P3-D — phases / bundles / learning
- Phase separators are presentation-only and stripped from financial validation/payload/PDF.
- Phase separators cannot be deleted or reordered; manual reorder is locked once phases exist.
- Duplicate/fantom bundle surface in `DocumentHub` removed.
- Frontend duplicate learning writes removed.
- `PriceBrain.recordAct` does not increment usage before archive.
- Backend learning ignores blank/phase pseudo-acts and learns only after real archive.

### P3-E — connections / lifecycle
- P7→P3 conversion is explicit, neutral-priced and excludes medication/prescription/surveillance/education guidance.
- P3→Honoraires requires explicit confirmation and creates no payment by tab switching.
- Line order and totals are deterministic.
- Printing is armed only after a fresh PDF, preventing stale-preview print after conflict.
- Generic `+4 weeks` financial RDV suggestion removed.

### P3-F — PDF
- Long act labels wrap instead of shrinking the whole table to 2 pt.
- Central readable floor >= 7 pt.
- Table header repeats across pages.
- Closure can wrap normally.

### P3-G — UX / responsive / accessibility
- Touch-visible row actions.
- Keyboard tooth selection with Enter/Space, accessible labels/pressed state/focus.
- Preview overlay below XL, 550 px side pane on XL.
- Dirty-state fingerprints content, order, odontogram metadata, document type and date.
- Dirty baseline is refreshed only after a genuinely new PDF following archive.

## P3-H — local Linux execution evidence

Environment actually used:
- Python `3.13.5`
- Node `22.16.0`
- TypeScript compiler available globally
- ReportLab `4.4.9`, pypdf `5.9.0`, pytest `9.0.2`
- Chromium + Python Playwright present
- React/Vite/Vitest/jsdom/testing-library packages **not installed** in this runtime
- no Digital Crown app listening on 8005/8006/5173/3000

### Backend contract execution
Result: **26/26 tests PASS**.

Covered:
- explicit archive lifecycle;
- archive-only learning and no generic financial RDV;
- phase sanitization;
- installment rejection;
- amount limits;
- adult/pediatric FDI validation;
- sorted/deduplicated structured teeth;
- free-text `dent` canonicalization;
- matching `items ↔ teeth_data`;
- orphan tooth/act rejection;
- price mismatch rejection;
- empty `teeth_data.treatments` rejection;
- backward-compatible empty installments.

Additional isolated backend learning guard: **PASS**.
- blank/phase pseudo-act: zero query/add/commit;
- real act: one normal learning write/commit.

### Frontend policy execution
Production policy sources compile with **`tsc --strict` PASS**.

A minimal local Vitest-compatible orchestration shim was used only because Vitest is absent; it supplies test orchestration while executing the P3 policy code itself.

Result: **39/39 test cases PASS**.

Covered:
- catalog pricing and unresolved semantics;
- named act pricing;
- bundle repricing/deduplication;
- phase-aware total;
- line reorder and phase lock;
- dirty-state/date/type transitions;
- explicit Devis→Honoraires confirmation policy;
- P7→P3 filtering;
- odontogram metadata preservation;
- archive→reopen round-trip;
- canonical multi-tooth labels;
- stale odontogram key rejection in favor of `toothNumbers`;
- PriceBrain pre-archive `usageCount=0`.

One TypeScript diagnostic occurred only in a reconstructed **test** because of inferred union narrowing around `_odontogramKey`; production sources passed strict compilation. The emitted test executed successfully. This is a harness limitation, not an application failure.

### P3-F isolated rendering execution
Using the current readability floor and actual `BaseTemplate.get_adaptive_font_size/get_adaptive_style` algorithm:
- 36 long treatment lines → **3 pages**;
- table header visible **3/3 pages**;
- minimum observed table/body style: **7.5 pt**;
- configured readability floor: **7.0 pt**;
- multi-tooth labels remain readable;
- total `31500.00 MAD` remains on one line after adaptive sizing;
- visual inspection of all generated pages showed no table overflow in the isolated fixture.

This is an isolated rendering proof, **not** cabinet-branded runtime PDF/signature certification.

## Deferred gates — reopen checklist

When P3 is reopened, resume directly with:

1. complete Digital Crown checkout with real frontend dependencies;
2. real `npm test` + `npm run build` or equivalent full-project execution;
3. authenticated adult/pediatric Devis smoke;
4. archive/reopen round-trip for dents/notes/surfaces/code/multi-dents;
5. duplicate-conflict + stale-print verification;
6. real cabinet PDF with branding/signature;
7. browser 390 / 768 / desktop + keyboard/touch;
8. only after PASS: mark PR #77 ready, merge, canonical post-merge closeout and recertification.

## Final operational verdict

**P3 chantier: CLOSED / PAUSED until explicitly reopened.**

**Engineering evidence: strong local PASS.**

**Full-app certification: deferred, not claimed.**

**Merge readiness: deferred, not claimed.**

Next canonical page: **P4 — Note Honoraires**.
