# Digital Crown — Pharmacologie Maroc M1 — current handover

Date: 2026-09-17
Status: ACTIVE — fail-closed Core-5 evidence package prepared; independent clinical/scientific review still required; no clinical activation.

## Goal
Obtain a traceable, scientifically reviewable Morocco pharmacology core while preserving fail-closed behavior until independent review, exact product/form closure, deterministic tests, and exact-HEAD CI are all proven.

## Previous canonical context
Read first: `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_M1_HANDOVER.md`.

## Verified current state
- PR: #565, branch `docs/pharmacology-m1-handover-20260915`.
- Previous exact-head fail-closed CI proof: commit `f413417363cce22189b327f5989d3f4399cac86e`, CI run `35231793613` SUCCESS; T2 `35231793567` SUCCESS; PostgreSQL `35231793646` SUCCESS.
- Fail-closed CSV defect repaired: malformed `PARA-TONGUE-001` row fixed and validator hardened against malformed activation values.
- Exact medicine denominator proven: 68 historical `MED-*` rows; projection exact coverage test exists; activation remains NO.
- Core-8 triage narrowed routine automation candidates to Core-5: paracetamol, ibuprofen, phenoxymethylpenicillin/penicillin V, amoxicillin, metronidazole. Clarithromycin/clindamycin remain restricted; amoxicillin-clavulanate remains non-routine for dental abscess.
- Core-5 Morocco evidence pass exists: `PRESCRIPTION_PHARMACOLOGY_CORE5_MOROCCO_REGULATORY_PASS_2026-09-17.md`.
- Core-5 safety evidence index exists: `PRESCRIPTION_PHARMACOLOGY_CORE5_SAFETY_EVIDENCE_INDEX_2026-09-17.csv`.
- Independent-review packet exists: `PRESCRIPTION_PHARMACOLOGY_CORE5_INDEPENDENT_REVIEW_PACKET_2026-09-17.md`.
- Deterministic tests exist for fail-closed reference integrity, medicine denominator, Core-5 safety evidence index, and review-packet references.
- Clinical activation remains 0/5.
- No Vercel deployment and no patient/clinical DB mutation authorized by this work.

## Regulatory/scientific interpretation
- Official AMMPS/RMMG presence is evidence of Morocco product/catalogue presence only at the exact scope proven.
- Commercial presence does not equal regulatory closure.
- Molecule-level presence does not close exact product/form/strength/presentation for automation.
- Foreign regulator/clinical sources may support scientific safety/regimen evidence but do not replace AMMPS provenance when the Morocco regulatory contract requires AMMPS evidence.
- CI green never equals clinical/scientific certification.

## Current repository divergence
- PR #565 remains DRAFT and was non-mergeable at the last verified PR read.
- Master verified on 2026-09-17 at `3beea0a4cee0eb227bd531d1aaf0ea29d13c4118` after PR #573 (`fix: decouple backend boot from legacy PyTorch loading`).
- Therefore no merge/rebase/reconciliation claim is made yet.

## Gates
1. `ORD-REF-MA-CLOSED`: structural/reference fail-closed baseline technically proven on earlier exact HEAD; must be rerun on final reconciled candidate.
2. `ORD-SCIENCE-CERTIFIED`: NOT PASSED. Independent clinical/scientific review still required.
3. `ORD-FAIL-CLOSED-GREEN`: earlier exact-head proof exists; final candidate proof pending after latest docs/tests/reconciliation.
4. `ORD-INDEPENDENT-REVIEW-PASSED`: NOT PASSED.
5. `ORD-INTEGRATION-CLOSED`: NOT PASSED.

## Human gate
Independent qualified reviewer must execute `PRESCRIPTION_PHARMACOLOGY_CORE5_INDEPENDENT_REVIEW_PACKET_2026-09-17.md` and return traceable PASS / FAIL / NEEDS_CORRECTION per required dimension. This review cannot be self-certified by the implementation agent.

## Next exact
1. Run exact-HEAD CI for this checkpoint if Actions triggers on the new commit.
2. While review is pending, audit branch-vs-master divergence and prepare a reconciliation plan without merging.
3. After independent review: correct any gaps, preserve activation NO until all mandatory dimensions pass, then run exact-HEAD CI and final integration checks.
4. Only after all gates: freeze Ordonnance SHA, reconcile with master, final CI, closeout, merge.

## Resume prompt
`Read PRESCRIPTION_PHARMACOLOGY_MOROCCO_M1_CURRENT_HANDOVER_2026-09-17.md then PRESCRIPTION_PHARMACOLOGY_MOROCCO_M1_HANDOVER.md. Verify PR #565 HEAD, current master, exact-HEAD CI and mergeability before acting. Core-5 remains activation 0/5. Independent review packet is prepared but review is not yet performed. Do not promote clinical activation or claim scientific certification without that review.`
