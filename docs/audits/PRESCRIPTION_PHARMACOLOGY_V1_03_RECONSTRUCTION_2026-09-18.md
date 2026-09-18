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

## Extraction decisions and contradictions

Accepted into the clean reconstruction:
- structural master inventory and historical/addenda mappings required to prove denominator and identity integrity;
- para canonical/gap/addenda/entity maps required to prove target reachability and non-destructive overlap handling;
- medicine current-status projection strictly as a documentary gap ledger, with all 68 rows inactive;
- final #572 fail-closed validator hardening, medicine-gap audit, and their negative tests.

#572 supersedes the stale #565 versions where they differ:
- the `PARA-TONGUE-001` canonical row uses the repaired schema/cardinality from #572;
- blank `clinical_activation` is an explicit failure instead of a crash/implicit value;
- malformed CSV rows with unexpected or missing columns fail closed.

Intentionally not reconstructed in this structural batch:
- Core8 activation triage and candidate classifications;
- Core5 or other clinical/regimen/safety passes that would require accepting indication, dose, duration, pediatric, contraindication, interaction or specialist-boundary claims;
- stale operational handovers, intermediate progress notes and superseded audit snapshots.

Reason: those assets can be preserved as historical evidence in #565/#572, but this V1 reconstruction does not promote their clinical assertions to an accepted current reference without a fresh qualified source review.

## Exact-head evidence
The pharmacology deterministic gate must prove, on the final candidate HEAD:
- targeted documentary tests green;
- `scripts/validate_pharmacology_reference.py` green;
- deterministic medicine-gap report green;
- independent deterministic safety oracle green.

A green deterministic gate remains explicitly **not scientific approval**.
