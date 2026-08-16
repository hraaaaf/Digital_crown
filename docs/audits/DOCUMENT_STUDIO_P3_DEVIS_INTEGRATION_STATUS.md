# Document Studio P3 — Devis Integration Status

Date: 2026-08-16
Branch: `agent/p3d-devis-phases-learning`
Latest functional head with targeted local execution: `475b2955ea4393f5e2720a86ae9c96ba763c6f6f`
Full-repository certification harness commit: `f2c02697f84b06a008fa986c81361aa68bdd231d`

## Scope integrated

This branch carries P3-A through P3-G plus additional defects found during P3-H review. P3-H now has substantial targeted execution evidence, but the complete integrated application is still not certified because the repository CI runner/full authenticated runtime is unavailable.

### P3-A — financial isolation / backend contract
- Devis payload excludes installments and global-note semantics.
- Backend rejects non-empty Devis installments.
- Devis requires at least one real item after phase-row sanitization.
- Empty acts, negative/excessive amounts and invalid adult/pediatric FDI numbers are rejected.
- Structured `dents` is canonical over free-text `dent`.
- Devis generation no longer archives implicitly; archive must be requested.

### P3-B — odontogram source of truth
- Accounting rows are the canonical tooth/document source.
- Multi-tooth labels use the same representation in UI/backend/PDF (`14, 15, 16`).
- `teeth_data` is derived from canonical `toothNumbers`, never a stale `_odontogramKey`.
- Backend rejects orphan/inconsistent `teeth_data`: same tooth, act and price must exist in a real Devis item.
- Odontogram metadata persists on quote rows: treatment code, surfaces and notes.
- Archived Devis reopening now rehydrates `items + teeth_data` into structured accounting rows.
- Archived notes/surfaces are surfaced back into `TreatmentSelector` and preserved if the practitioner validates without changing them.

### P3-C — catalog pricing / dentition modes
- Managed catalog price is authoritative for catalog selections.
- Missing catalog price fails closed to unresolved/zero rather than stale remembered price.
- Adult and pediatric odontograms have separate valid quick groups.
- Pediatric teeth are accepted by the treatment selector.
- Named/global/group shortcuts are repriced through the managed catalog.

### P3-D — phases / bundles / learning
- Phase separators are presentation-only and stripped before Devis validation/PDF.
- Phase rows are non-financial in validation, totals, payload and UI editing.
- Manual reorder is locked when phase separators exist so acts cannot cross phase boundaries accidentally.
- Duplicate DocumentHub bundle engine removed; AccountingStudio is the single visible Devis bundle surface.
- Bundle prices resolve through the managed catalog; unresolved amounts remain explicit.
- Frontend duplicate act-learning writes removed.
- `PriceBrain.recordAct` keeps `usageCount` unchanged and is only local price memory.
- Financial act learning occurs only after real archive.
- Backend learning rejects blank and phase-separator pseudo-acts.

### P3-E — connections / lifecycle
- Treatment-plan result can explicitly create a neutral Devis.
- Non-financial plan proposals such as prescriptions, antibiotics, surveillance and education are excluded from automatic P7→P3 financial conversion.
- Plan conversion does not invent prices.
- Devis→Honoraires transition requires explicit confirmation and states that no payment is created by tab switching.
- Manual lines can be moved up/down on non-phased Devis.
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

These are real local executions reconstructed from the connected GitHub source. They do not replace a complete repository run or authenticated browser smoke.

### Backend targeted execution
- Current Devis schema/lifecycle/phase contracts were replayed locally with Pydantic/pytest.
- Latest targeted suite: **19 passed**, 1 unrelated existing Pydantic class-based Config deprecation warning on `DocumentArchiveOut`.
- Covered: explicit archive, archive-only learning, no generic financial RDV, phase sanitization, installment rejection, amount limits, FDI validation, canonical structured teeth, matching `items ↔ teeth_data`, orphan/mismatched teeth-data rejection and backward-compatible empty installments.
- Additional isolated learning guard: **PASS** for blank/phase pseudo-act rejection while real act learning still writes normally.

### Frontend pure-policy execution
- Pure TypeScript policy modules compile with `tsc --strict` in the isolated harness.
- Pricing/bundles/order/total/plan-conversion/learning policies: **22/22 assertion groups passed**.
- Odontogram source/mode/metadata/round-trip policies: **10/10 groups passed**.
- Latest canonical-teeth-data regression: **5/5 assertions passed**, including stale `_odontogramKey=21` with canonical `toothNumbers=[16]` producing tooth 16 metadata.
- `PriceBrain` local-memory behavior: **1/1 passed**; repeated price edits leave `usageCount` unchanged before archive.

### P3-F isolated rendering execution
- A5 fixture with 36 long treatment lines rendered successfully to **3 pages**.
- Table header detected on **3/3 pages**.
- Minimum observed paragraph font size: **7.5 pt**.
- Minimum requested adaptive floor: **7.0 pt**.
- Long labels and `TOTAL GÉNÉRAL` were present in extracted PDF text.
- This proves targeted multipage/readability behavior, not the complete cabinet-branded PDF runtime.

## Full-repository certification harness

`scripts/certify_p3_devis.sh` is the canonical automated P3-H resume path.

It fails closed and mirrors the repository CI gates:
1. clean Git worktree;
2. Python 3.12 and Node 20;
3. positive development production-safety gate;
4. targeted P3 Devis backend regressions;
5. full backend test suite with `--maxfail=1`;
6. full frontend `npm test`;
7. frontend production build with `npm run build`;
8. negative production-safety gate must reject intentionally unsafe config;
9. exact tested Git head is printed;
10. no merge/production-ready claim while manual gates remain open.

`bash -n` passed in the isolated runtime. That runtime is Python 3.13 / Node 22, so the full harness correctly refuses to impersonate the CI environment and has not been executed there.

## Current GitHub CI blocker

- Repeated P3 runs fail before runner execution with jobs returning `steps: null` and no job logs.
- Latest previously inspected run: **31923726341** (#415), all 3 jobs `steps:null`.
- GitHub connector lacks repository Actions-admin and Billing scopes; direct Actions-permissions/runners/Billing diagnostics return authorization errors.
- Replit fallback is unavailable without an active subscription/runtime agent.
- Vercel connection contains AkarFinder only; no Digital Crown runtime is exposed.
- Local container cannot clone GitHub because outbound DNS to `github.com` is unavailable.

This is external infrastructure evidence, not a passing or failing application test result.

## P3-H manual gates still required

After `bash scripts/certify_p3_devis.sh` passes on the exact candidate head:

### Runtime authenticated smoke
- adult Devis: create, catalog select/unresolved price, odontogram edit, line edit/reorder/delete, preview;
- pediatric Devis: create, Q5-Q8 groups, odontogram edit, preview;
- archived Devis reopen: treatment code, surfaces, notes and teeth round-trip intact;
- phased Devis: separators remain presentation-only and manual reorder cannot cross phases;
- P7→P3: clinical/non-financial recommendations do not become financial rows;
- P3→Honoraires: explicit confirmation, no implicit payment creation;
- explicit archive only;
- duplicate conflict path never prints stale preview;
- print uses the newly generated PDF;
- no generic 4-week RDV suggestion;
- no inherited P5 installments/global-note state enters Devis.

### Cabinet PDF visual smoke
- short Devis;
- long/multipage Devis;
- signature present/absent;
- adult and pediatric teeth;
- multi-tooth label identical UI/PDF (`14, 15, 16`);
- no text below central readability floor.

### Responsive/accessibility smoke
- 390 px;
- 768 px;
- desktop/XL;
- row move/delete usable on touch layouts;
- odontogram direct tooth selection usable by keyboard Enter/Space;
- preview overlay/pane behavior matches breakpoint contract.

## Exact resume sequence

1. Restore a real runner or open a complete local clone on the P3 candidate branch.
2. Run `bash scripts/certify_p3_devis.sh` from repository root.
3. On failure: diagnose → fix → rerun the smallest relevant gate → rerun full harness.
4. Execute authenticated runtime/PDF/responsive smoke above.
5. Only after all automated + manual gates pass: mark PR ready, reconcile/merge to current master, update canonical ROADMAP/SESSION/STATUS/CHANGELOG as applicable, and run post-merge certification.

## Certification status

**NOT CERTIFIED / NOT MERGE-READY.**

P3-A→P3-G and the defects found during P3-H review are now substantially hardened with targeted execution evidence. The remaining blocker is integrated full-repository/runtime certification, not a known unaddressed P3 logic defect.
