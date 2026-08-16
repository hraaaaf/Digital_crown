# Document Studio P3 — Devis Integration Status

Date: 2026-08-16
Branch: `agent/p3d-devis-phases-learning`
Functional code head locally re-executed: `e25c01f63fbe4e1625f2b53751efedd57d9cefd9`
Full-repository certification harness: `scripts/certify_p3_devis.sh`

## Scope integrated

P3-A through P3-G are integrated on the branch, including defects found during P3-H review. P3-H now has substantial **local Linux execution evidence** independent of GitHub Actions. The full authenticated React application is still not certified because this runtime does not contain the complete checkout/frontend dependency tree.

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
A Devis-relevant package was reconstructed from the current branch source and the P3 contract tests were materialized locally.

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
Production policy sources were materialized from the current branch and compile with **`tsc --strict` PASS**.

A minimal local Vitest-compatible orchestration shim was used only because the Vitest package is absent; it supplies `describe/it/expect/beforeEach/vi` while executing the P3 policy code itself.

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

One TypeScript diagnostic occurred only in a reconstructed **test** because of inferred union narrowing around `_odontogramKey`; production sources still passed strict compilation. The emitted test was executed successfully. This is a harness limitation, not represented as an application PASS or failure.

### P3-F isolated rendering execution
Using the current P3 readability floor and the actual `BaseTemplate.get_adaptive_font_size/get_adaptive_style` algorithm:
- 36 long treatment lines → **3 pages**;
- table header visible **3/3 pages**;
- minimum observed table/body style: **7.5 pt**;
- configured readability floor: **7.0 pt**;
- multi-tooth labels remain readable;
- total `31500.00 MAD` remains on one line after adaptive sizing;
- visual inspection of all generated pages showed no table overflow in the isolated fixture.

This is an isolated rendering proof, **not** a cabinet-branded runtime PDF/signature certification.

## GitHub Actions status

GitHub Actions is **not part of the active P3-H path**. Its runner-allocation problem is recorded only as infrastructure history and is not treated as a blocker or code verdict for this chantier.

## Remaining P3-H gates

### Full application build/runtime
Still required:
- complete Digital Crown checkout with real frontend dependencies;
- real `npm test` / `npm run build` or equivalent full-project execution;
- authenticated Devis runtime.

### Authenticated smoke
- adult Devis create/catalog/odontogram/edit/reorder/delete/preview;
- pediatric Q5-Q8 path;
- explicit archive and archive reopen;
- notes/surfaces/code/multi-dent round-trip;
- phased Devis behavior;
- P7→P3 filtered conversion;
- P3→Honoraires explicit conversion;
- duplicate conflict + stale print prevention.

### Cabinet PDF / responsive
- real cabinet branding + signature fixture;
- short and long adult/pediatric Devis;
- 390 / 768 / desktop browser inspection;
- touch controls and odontogram keyboard interaction.

## Certification status

**P3-A→P3-G: substantially hardened with current local execution evidence.**

**P3-H: NOT YET FULL-APP CERTIFIED / NOT YET MERGE-READY.**

The remaining gap is the complete authenticated React application/build and cabinet/browser smoke, not a currently known unaddressed P3 policy/backend/PDF logic defect.
