# Digital Crown V1-07 — Global Interactive Audit — G10 Closeout

Status: NOT READY — PREPARED FOR FINAL CLOSEOUT

## Goal
Close V1-07 only after G0→G9 are certified on one exact final HEAD, then merge and verify post-merge before unblocking V1-08.

## Success
All of the following are observable on the same final candidate:
1. G0 final inventory run is green.
2. G1→G8 canonical audit files are certified or explicitly reconciled with verified reusable proof.
3. G1 Landing + G6/G7 UI remediations have matched true BEFORE/AFTER evidence at the required viewports and a recorded visual comparison/score.
4. G9 semantic denominator is frozen with zero known critical untested controls.
5. Frontend tests + build are green on exact HEAD.
6. The final candidate passes the independent V1-07 pre-freeze safety requirements on the same code: full backend regression plus the required Windows/runtime/PostgreSQL/Alembic contracts.
7. Relevant visual/runtime certifications required by changed surfaces are green.
8. PR #633 is coherent, non-draft only when ready, mergeable, and contains no unresolved audit blocker.
9. Canonical docs and Notion reflect only verified state.
10. Merge is performed only after the above gates.
11. Post-merge exact commit is verified by required workflows, including the master-only cabinet release certification.
12. V1-08 is unblocked only after post-merge proof.

## Current blockers
- exact-head PR CI is pending;
- exact-head G0 rerun is pending;
- G1/G6/G7 matched BEFORE/AFTER workflow is pending (21 matched captures required: 7 scenarios × 3 viewports);
- visual comparison/score is not yet recorded;
- final-candidate full backend regression has not yet been dispatched;
- final-candidate Windows Build Dependency Contract / PostgreSQL Alembic Schema Certification / Cabinet Upgrade PostgreSQL Certification have not yet been certified on the final candidate;
- G9 semantic denominator is not frozen.

## Closeout sequence
1. Stabilize one final PR HEAD and keep it synchronized with current `master`.
2. Read exact-head PR CI, G0 and truth-safety visual evidence.
3. Diagnose/fix any failure; any code/doc change creates a new candidate and invalidates prior exact-head proof.
4. Inspect BEFORE/AFTER artifacts and record matched scenarios/viewports + visual score.
5. Update G1/G6/G7/G8 canonical statuses only to the level proved.
6. Reconcile final G0 output with G1→G8 proof registry and adjudicate every remaining inspection row semantically.
7. On that same final candidate, run exactly once the heavy pre-freeze certifications:
   - `CI` via `workflow_dispatch` to include **Full backend regression** (PR-triggered CI does not run it);
   - `Windows Build Dependency Contract` via `workflow_dispatch`;
   - `PostgreSQL Alembic Schema Certification` via `workflow_dispatch`;
   - `Cabinet Upgrade PostgreSQL Certification` via `workflow_dispatch`.
8. Freeze G9 semantic denominator only if zero known critical gaps and all pre-freeze BLOCKER/MUST-FIX findings remain remediated.
9. Update all canonical audit files and Notion.
10. Verify PR #633 diff/coherence/mergeability; mark ready only when all pre-merge gates are satisfied.
11. Merge.
12. Verify the exact post-merge `master` commit with normal post-merge CI/upgrade gates.
13. Dispatch `Cabinet Certified Release` only against the exact current immutable `master` HEAD, as required by that workflow.
14. Update final closeout record and only then unblock V1-08.

## Deployment
No Vercel deployment is part of V1-07 closeout unless explicitly authorized by the product owner.


## Candidate PR composition
Do not pin an intermediate SHA/file count here. Recompute PR composition only after the final candidate is intentionally stabilized.

Expected direct runtime/product mutations currently include:
- `frontend/src/pages/LandingPage.tsx`;
- `frontend/src/pages/LicenseStatusPage.tsx`;
- `frontend/src/pages/StockPage.tsx`;
- `frontend/src/main.tsx` + `telemetryPolicy.ts` for explicit frontend telemetry opt-in;
- `backend/main.py` for root health exception redaction.

All other changes must remain explainable as audit tests, evidence harness/workflows, inventory/reconciliation tooling, canonical documentation, or explicitly inherited master synchronization. Recompute and verify this claim from the final PR diff before closeout.
