# Document Studio P3 — Devis Integration Status

Date: 2026-08-16
Branch: `agent/p3d-devis-phases-learning`
Application functional head verified with targeted execution: `c7385e2affdcfcef049c524f18f71138925c102a`
Full-repository certification harness commit: `f2c02697f84b06a008fa986c81361aa68bdd231d`

## Scope integrated

This branch carries the implementation work for P3-A through P3-G. P3-H has static inspection evidence, targeted local execution evidence and now a fail-closed full-repository certification harness, but the complete integrated application is not certified yet.

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
- Committed behavioral assertions were replayed in Node because Vitest is not installed in the local isolated execution image.
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

## Full-repository certification harness

`scripts/certify_p3_devis.sh` is the canonical automated P3-H resume path.

It mirrors the repository CI gates and fails closed:
1. requires a clean Git worktree;
2. requires **Python 3.12** and **Node 20**, matching `.github/workflows/ci.yml`;
3. runs the positive development `prod_safety_check.py` gate;
4. runs targeted P3 Devis backend regressions;
5. runs the full backend test suite with `--maxfail=1`;
6. runs the full frontend `npm test` suite;
7. runs the frontend production build via `npm run build`;
8. runs the negative production-safety gate and requires the intentionally unsafe production config to be rejected;
9. prints the exact tested Git head;
10. explicitly refuses to imply production/merge readiness while the manual gates remain open.

The script syntax was checked successfully with `bash -n` in the isolated runtime. That runtime exposes Python 3.13 / Node 22, so the script correctly refuses to masquerade as the CI environment; the full harness has therefore **not** been executed here.

## Current GitHub CI blocker

- Functional-head run **31923178969** (#395), head `c7385e2affdcfcef049c524f18f71138925c102a`: `failure` with `steps: null` on all three jobs, meaning no GitHub-hosted test/build started.
- Harness-head run **31923680764** (#414), head `f2c02697f84b06a008fa986c81361aa68bdd231d`: first check returned `queued`. Per project CI policy it is not polled while independent work remains.
- Earlier P3 runs show the same runner-allocation / Billing-spending-limit condition. This is external infrastructure evidence, not a code-test failure.

## Alternative full-repo execution paths investigated

- Local container: Git is available but outbound DNS to `github.com` fails, so the full repository cannot be cloned there.
- Replit: no Digital Crown app exists; the only plausible old clinic app has no registered Replit agent and cannot be inspected/executed through the connector.
- Vercel: connected account contains only the AkarFinder project; no Digital Crown project or executable Sandbox tool is exposed in this session.

## P3-H manual gates still required

After `scripts/certify_p3_devis.sh` passes on the exact candidate head:

### Runtime authenticated smoke
- adult Devis: create, edit, reorder, preview;
- pediatric Devis: create, edit, groups Q5-Q8, preview;
- explicit archive only, then reopen/archive evidence;
- duplicate conflict path must never print a stale preview;
- print path must use the newly generated PDF;
- verify no Devis-created generic 4-week RDV suggestion;
- verify no inherited P5 installments/global-note state enters the Devis.

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
- row move/delete controls usable on touch layouts;
- odontogram tooth selection usable by keyboard Enter/Space;
- preview overlay/pane behavior matches breakpoint contract.

## Exact resume sequence

1. Restore a real runner or open a full local clone on the P3 candidate branch.
2. Run `bash scripts/certify_p3_devis.sh` from the repository root.
3. If any automated gate fails: diagnose → fix → rerun the smallest relevant gate → rerun the full harness.
4. Execute the authenticated runtime/PDF/responsive smoke checklist above.
5. Only when all automated + manual gates pass: mark PR ready, reconcile/merge to the current master baseline, update canonical ROADMAP/SESSION/STATUS/CHANGELOG as applicable, and run post-merge certification.

## Certification status

**NOT CERTIFIED / NOT MERGE-READY.**

No full-repository CI/build has executed on the integrated branch and no authenticated full-app Devis smoke has passed yet. No production-readiness claim is made.
