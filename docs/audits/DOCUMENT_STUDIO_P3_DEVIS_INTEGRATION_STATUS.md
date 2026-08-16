# Document Studio P3 — Devis Integration Status

Date: 2026-08-16
Branch: `agent/p3d-devis-phases-learning`
Latest functional head with targeted local execution: `475b2955ea4393f5e2720a86ae9c96ba763c6f6f`
Latest additional functional head statically reviewed: `0cd472a10124dcba74debd1dee06eeff7e9554f1`
Full-repository certification harness commit: `f2c02697f84b06a008fa986c81361aa68bdd231d`

## Scope integrated

This branch carries P3-A through P3-G plus defects found during P3-H review. P3-H has substantial targeted execution evidence, but the complete integrated application is still not certified because the repository CI runner/full authenticated runtime is unavailable.

### P3-A — financial isolation / backend contract
- Devis payload excludes installments and global-note semantics.
- Backend rejects non-empty Devis installments.
- Devis requires at least one real item after phase-row sanitization.
- Empty acts, negative/excessive amounts and invalid adult/pediatric FDI numbers are rejected.
- Structured `dents` is canonical over free-text `dent`.
- Devis generation no longer archives implicitly; archive must be requested.

### P3-B — odontogram source of truth
- Accounting rows are the canonical tooth/document source.
- Multi-tooth labels use the same UI/backend/PDF representation (`14, 15, 16`).
- `teeth_data` derives from canonical `toothNumbers`, never a stale `_odontogramKey`.
- Backend rejects orphan/inconsistent `teeth_data`: same tooth, act and price must exist in a real Devis item.
- Treatment code, surfaces and notes persist on quote rows.
- Archived Devis reopening rehydrates `items + teeth_data` into structured accounting rows.
- Archived notes/surfaces are surfaced back into `TreatmentSelector` and preserved if unchanged.

### P3-C — catalog pricing / dentition modes
- Managed catalog price is authoritative.
- Missing catalog price fails closed to unresolved/zero rather than stale remembered price.
- Adult and pediatric quick groups are separated.
- Pediatric teeth are accepted by the selector.
- Named/global/group shortcuts are repriced through the managed catalog.

### P3-D — phases / bundles / learning
- Phase separators are presentation-only and stripped before Devis validation/PDF.
- Phase rows are non-financial in validation, totals, payload and UI editing.
- Reorder is locked when phase separators exist so acts cannot cross phase boundaries accidentally.
- AccountingStudio is the single visible Devis bundle surface.
- Bundle prices resolve through the catalog; unresolved amounts stay explicit.
- Frontend duplicate learning writes removed.
- `PriceBrain.recordAct` keeps `usageCount` unchanged before archive.
- Financial act learning occurs only after real archive.
- Backend learning rejects blank and phase-separator pseudo-acts.

### P3-E — connections / lifecycle
- Treatment-plan result can explicitly create a neutral Devis.
- Non-financial plan proposals such as prescriptions, antibiotics, surveillance and education are excluded from automatic P7→P3 financial conversion.
- Plan conversion does not invent prices.
- Devis→Honoraires requires explicit confirmation and states that no payment is created by tab switching.
- Manual lines can be moved on non-phased Devis.
- Total uses one phase-aware policy.
- Printing is armed only after a fresh PDF is returned, preventing stale-preview printing after conflicts.
- Generic financial-document RDV suggestion with hard-coded 4-week interval removed.

### P3-F — professional PDF
- Long act labels wrap instead of forcing a 2 pt uniform font.
- Central readable typography floor is enforced (>= 7 pt).
- Table headers repeat across pages.
- Closure text can wrap without all-NBSP shrinking.

### P3-G — UX / responsive / accessibility
- Row move/delete controls are visible on touch-sized layouts.
- Direct odontogram tooth selection supports keyboard Enter/Space, labels, pressed state and focus indication.
- Preview becomes full-overlay below XL and fixed 550 px side pane on XL desktop.
- Non-authoritative fallback treatment durations and the misleading duration column were removed at `0cd472a1…`.

## Executed P3-H evidence

These are real local executions reconstructed from connected GitHub source. They do not replace a complete repository run or authenticated browser smoke.

### Backend targeted execution
- Latest targeted suite: **19 passed**, 1 unrelated existing Pydantic class-based Config deprecation warning on `DocumentArchiveOut`.
- Covered explicit archive, archive-only learning, no generic financial RDV, phase sanitization, installment rejection, amount limits, FDI validation, canonical structured teeth, matching `items ↔ teeth_data`, orphan/mismatched teeth-data rejection and backward-compatible empty installments.
- Additional isolated learning guard: **PASS** for blank/phase pseudo-act rejection while real act learning still writes normally.

### Frontend pure-policy execution
- Pure policy modules compile with `tsc --strict` in the isolated harness.
- Pricing/bundles/order/total/plan-conversion/learning: **22/22 assertion groups passed**.
- Odontogram source/mode/metadata/round-trip: **10/10 groups passed**.
- Canonical-teeth-data regression: **5/5 assertions passed**, including stale `_odontogramKey=21` with canonical `toothNumbers=[16]` producing tooth 16 metadata.
- `PriceBrain`: **1/1 passed**; repeated price edits leave `usageCount` unchanged before archive.
- The later `0cd472a1…` duration-removal commit was statically reviewed as a single-file deletion-only UX cleanup; it has not been represented as a new runtime/build PASS.

### P3-F isolated rendering execution
- A5 fixture with 36 long treatment lines rendered to **3 pages**.
- Table header detected on **3/3 pages**.
- Minimum observed paragraph font size: **7.5 pt**.
- Adaptive floor requested: **7.0 pt**.
- Long labels and `TOTAL GÉNÉRAL` present in extracted PDF text.

## Full-repository certification harness

`scripts/certify_p3_devis.sh` is the canonical P3-H resume path. It fails closed and mirrors repository CI: clean worktree, Python 3.12, Node 20, positive safety gate, targeted P3 regressions, full backend suite, `npm test`, `npm run build`, negative safety gate and exact SHA output. It does not imply merge readiness while manual gates remain open.

`bash -n` passed in the isolated runtime. That runtime is Python 3.13 / Node 22, so the full harness correctly refuses to impersonate CI and has not been executed there.

## Current GitHub CI blocker

- Repeated P3 runs fail before runner execution with `steps: null` and no job logs.
- Latest previously inspected run: **31923726341** (#415), all 3 jobs `steps:null`.
- GitHub connector lacks Actions-admin/Billing scopes.
- Replit fallback unavailable without active subscription/runtime agent.
- Vercel exposes no Digital Crown runtime.
- Local container cannot clone GitHub because outbound DNS to `github.com` is unavailable.

This is infrastructure evidence, not an application test result.

## P3-H manual gates still required

After `bash scripts/certify_p3_devis.sh` passes on the exact candidate head:

### Runtime authenticated smoke
- adult Devis: create, catalog select/unresolved price, odontogram edit, line edit/reorder/delete, preview;
- pediatric Devis: create, Q5-Q8 groups, odontogram edit, preview;
- archived reopen: treatment code, surfaces, notes and teeth round-trip intact;
- phased Devis: separators presentation-only and reorder cannot cross phases;
- P7→P3: non-financial clinical recommendations do not become financial rows;
- P3→Honoraires: explicit confirmation, no implicit payment;
- explicit archive only;
- duplicate conflict never prints stale preview;
- print uses newly generated PDF;
- no generic 4-week RDV;
- no inherited P5 installments/global-note state in Devis.

### Cabinet PDF visual smoke
- short and long/multipage Devis;
- signature present/absent;
- adult and pediatric teeth;
- multi-tooth UI/PDF label equality;
- no text below readability floor.

### Responsive/accessibility smoke
- 390 px, 768 px, desktop/XL;
- move/delete usable on touch;
- odontogram tooth usable by Enter/Space;
- preview overlay/pane matches breakpoint contract.

## Exact resume sequence

1. Restore a real runner or open a complete local clone.
2. Run `bash scripts/certify_p3_devis.sh`.
3. On failure: diagnose → fix → smallest relevant gate → full harness.
4. Execute authenticated runtime/PDF/responsive smoke.
5. Only after all PASS: mark PR ready, reconcile/merge to current master, update ROADMAP/SESSION/STATUS/CHANGELOG as applicable, then post-merge certification.

## Certification status

**NOT CERTIFIED / NOT MERGE-READY.**

P3-A→P3-G and the defects found during P3-H are substantially hardened with targeted execution evidence. The remaining blocker is integrated full-repository/runtime certification, not a known unaddressed P3 logic defect.
