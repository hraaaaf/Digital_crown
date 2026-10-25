# LOT05/J15 — Private staging safety plan (PRE, 2026-10-25)

## Scope
The current J13 private staging engine still enforces an **obsolete 21-relabel / 10-unresolved** decision census. The owner-private V22 clinical review has moved beyond those counters. **Do not bypass J13's hard-coded validation, forge an old manifest, or execute real staging against a newer manifest.**

J15 is an explicit fail-closed **planning gate**: synthetic-only summary with fixed source pin, 266/33/34 partition census, integer counts, original-preservation boolean, unresolved/primary/collision/deduplication blockers, and separate checks for private geometry QA and engine integration. It never reads the owner-private manifest, individual case identifiers, JPEGs, or original YOLO annotations.

## Evidence
- 12 synthetic tests in `experiments/test_lot05_j15_private_staging_plan.py`.
- Standalone `experiments/lot05_j15_private_staging_plan.py` prints an aggregate **blocked** status only.
- Existing 15 J13 + 13 J14 synthetic tests and 333/333 pinned source TXT read-only census remain required in the workflow.

## Next real work, only on authorized private workstation
1. Confirm current V22 manifest and review lineage, private permissions and source commit.
2. Design a versioned private manifest migration with explicit status for **confirmed permanent / confirmed primary / tentative / unresolved / superseded**, including box-level witnesses and no silent coercion.
3. Integrate the J14 ontology gate into the actual private correction engine, not merely a public preflight.
4. Reconcile **all** collision groups and exact duplicate deletions under independent clinical adjudication.
5. Test private source integrity, output atomicity, and 333/333 count on a *synthetic fixture* before any real source access.
6. Keep staging blocked until all gates are green; then create a new owner-private, non-Git copy only under separate explicit approval.

No real corrected dataset, no training, no merge, no Vercel/Production deployment, no clinical release. Commercial license and patient-level independence remain unresolved.
