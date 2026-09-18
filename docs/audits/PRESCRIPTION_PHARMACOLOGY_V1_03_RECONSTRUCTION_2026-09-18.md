# Digital Crown V1-03 — Pharmacology Morocco reconstruction

Date: 2026-09-18

## Goal
Reconstruct only machine-verifiable Morocco pharmacology reference assets from stale PRs #565/#572 on a clean branch from certified master.

## Safety boundary
- These files are documentary/audit evidence, not runtime prescribing rules.
- Imported historical/clinical status labels are preserved as source evidence and are not independently re-approved by this reconstruction.
- Every reconstructed CSV carrying `clinical_activation` must remain `NO`.
- No automatic prescribing, dose, duration, indication, pediatric, interaction, contraindication, renal/hepatic or specialist recommendation is activated by this lot.
- Core8 clinical triage and other evaluative clinical classifications from stale branches are intentionally excluded pending qualified independent scientific review.

## Provenance
- Structural reference source: stale PR #565 evidence lineage.
- Final fail-closed validator corrections and deterministic medicine-gap audit: stale PR #572.
- Reconstructed onto certified master; neither stale branch is merged as-is.

## Machine-verifiable invariants
- 170 historical inventory rows and 170 historical mapping rows.
- 8 addendum rows mapped exactly once.
- 20 structural gap IDs.
- 173 historical target references with no dangling target.
- duplicate/overlap/boundary entities cannot auto-merge and require discriminators.
- 68 medicine rows represented exactly once in the current-status projection.
- all 68 projected medicines remain `clinical_activation=NO`.
- malformed CSV row cardinality and blank/non-NO activation values fail closed.

## Deferred scientific gate
Clinical activation remains prohibited until a qualified independent clinical/scientific review validates specific claims against current primary/authoritative sources and the resulting evidence is recorded separately.
