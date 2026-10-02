# Cephalo vNext — LOT04 Tolerance Policy — HUMAN GATE PROPOSAL

Status: APPROVED — HUMAN_GATE A / REFERENCE_EQUIVALENCE_V1; frozen before candidate scoring
Gate target: `CEPH_DETECTOR_SELECTED`
Branch preparation base: `c2da527a9622cf1a9493adb6f4770194d7bf8e3c`

## Purpose
Freeze the scientific decision space for quantitative acceptance **before** any SRPose38 anatomical scoring. This document does not select a detector and does not define universal clinical-validity thresholds.

## Observed project evidence
LOT02 Aariz evidence shows large landmark-specific variability. The direct anatomy-compatible mapping has 24 landmarks. Junior and Senior Aariz folders are aggregate annotations from junior and senior orthodontist phases; published Aariz ground truth is formed from group averages. Therefore the junior↔senior distances are useful dataset-specific uncertainty signals but are **not equivalent to two raw independent observer errors**.

| Aariz | DC | human median mm | human p95 mm |
|---|---|---:|---:|
| A | A | 0.288 | 1.966 |
| ANS | ANS | 0.144 | 2.246 |
| B | B | 0.490 | 2.927 |
| Me | Me | 0.791 | 2.324 |
| N | N | 0.200 | 1.891 |
| Or | Or | 0.600 | 3.455 |
| Pog | Pog | 0.089 | 1.390 |
| PNS | PNS | 0.000 | 0.985 |
| Pn | Prn | 0.000 | 1.283 |
| S | S | 0.000 | 0.457 |
| Ar | Ar | 0.000 | 2.220 |
| Co | Co | 0.322 | 3.401 |
| Gn | Gn | 0.378 | 1.418 |
| Go | Go | 0.825 | 4.142 |
| Po | Po | 0.823 | 4.342 |
| LIT | L1_incisal | 0.144 | 1.433 |
| UIA | U1_apex | 0.629 | 3.700 |
| UIT | U1_incisal | 0.144 | 1.391 |
| LIA | L1_apex | 0.447 | 2.985 |
| Li | Li_soft | 0.000 | 1.170 |
| Ls | Ls_soft | 0.000 | 0.709 |
| N` | N_soft | 0.000 | 1.552 |
| Pog` | Pog_soft | 0.000 | 1.334 |
| Sn | Sn_soft | 0.000 | 1.209 |

Sentinel measurement disagreement on the qualified G1-A subset:

| Measure | Unit | n G1-A | human median abs | human p95 abs |
|---|---:|---:|---:|---:|
| ANB | deg | 809 | 0.228 | 1.077 |
| Co-A | mm | 841 | 0.268 | 1.450 |
| Co-Gn | mm | 860 | 0.233 | 1.321 |
| FMA | deg | 535 | 0.602 | 2.246 |
| FMIA | deg | 632 | 1.035 | 3.965 |
| IMPA | deg | 659 | 1.007 | 3.734 |
| SN-GoGn | deg | 734 | 0.507 | 2.268 |
| SNA | deg | 907 | 0.314 | 1.476 |
| SNB | deg | 845 | 0.183 | 1.262 |

## Scientific evidence checked
- Khalid et al., Scientific Data 2025, DOI 10.1038/s41597-025-05542-3 / PMID 40745164: Aariz uses 1000 LCRs, 29 landmarks, seven devices; annotation/review is multi-orthodontist and reports intra/inter-observer variability.
- Polizzi et al., Journal of Dentistry 2024, PMID 38729291: umbrella review explicitly warns that conclusions commonly based on a 2 mm cut-off are not a sound universal clinical-validity basis; landmark accuracy is heterogeneous and final orthodontist supervision remains necessary.
- Durão et al., Dentomaxillofacial Radiology 2015, PMID 26730368: interobserver reproducibility differs substantially by landmark; Co, Gn, Or, ANS and related structures are among less reproducible points.
- Damstra et al., Am J Orthod Dentofacial Orthop 2010, PMID 21055590: measurement error differs by cephalometric variable; smallest detectable difference should be considered rather than assuming one universal tolerance.

## What the evidence supports
1. No global 2 mm clinical gate.
2. Landmark-specific and measurement-specific acceptance.
3. Human-reference uncertainty must be visible in the decision.
4. Aggregate MRE/SDR cannot hide a weak high-impact landmark.
5. Downstream angular/linear error must be evaluated separately.
6. Device/case strata must be reported; they should not silently redefine thresholds after scoring.
7. Clinical validity is not established by model-vs-reference distance alone.

## Proposed pre-scoring policy options

### Option A — strict reference-equivalence engineering gate
Use the frozen LOT02 human-reference envelope as a **non-clinical engineering selection bar**:
- per landmark: candidate p95 error must be <= the observed LOT02 human p95 for that same compatible landmark;
- per sentinel measurement: candidate p95 absolute error must be <= the observed G1-A human p95 for that measurement;
- no universal 2 mm rule;
- no unsupported SRPose-only identity can PASS;
- no silent/non-finite/out-of-frame output may be consumed clinically;
- fail-open rate must be exactly 0;
- fail-closed rate is reported separately and cannot be hidden by aggregate accuracy.

Rationale: this does not claim clinical acceptability; it asks the detector not to be worse than the project’s observed human-reference disagreement envelope. It is deliberately strict and may reject SRPose38.

Limitation: the Aariz human-reference envelope is based on aggregated annotation/review phases, not raw independent observer pairs, so the equivalence interpretation is conservative but imperfect.

### Option B — non-inferiority margin above human envelope
Allow a multiplicative or additive margin above the human p95.

**Not scientifically fixed by the sources reviewed.**
Any margin such as 10%, 20%, 25%, 0.5 mm or 1° would be a project/human decision unless independently justified for each endpoint. It must be frozen before model results.

### Option C — no detector-selection threshold yet
Keep `CEPH_DETECTOR_SELECTED` blocked until a qualified orthodontic human reviewer approves endpoint-specific clinical/non-inferiority margins. Environment identity, corpus integrity and manifest construction may proceed, but no candidate PASS/FAIL scoring is allowed.

## Recommendation for human gate
If the project owner wants to proceed without inventing clinical cut-offs, **Option A** is the cleanest auditable engineering gate. It is intentionally framed as detector selection relative to observed human-reference variability, not as proof of clinical validity.

The later Human Review and Clinical Validation lots remain mandatory even if Option A passes.

## Decisions that remain HUMAN_GATE_REQUIRED
1. Approve Option A, B or C.
2. If B: supply/approve the exact endpoint-specific margin and its rationale before candidate scoring.
3. Define an operational maximum fail-closed rate if anything above 0 is to be accepted. No evidence reviewed establishes one universal acceptable percentage.
4. Confirm whether a detector must PASS every compatible landmark/measurement, or whether any endpoint may remain VALIDATION_REQUIRED/RESEARCH_ONLY without blocking detector selection. Current LOT04 validator requires every reported endpoint to PASS for overall PASS.

## Stop
No candidate inference or acceptance scoring until this human gate is explicitly resolved and frozen in the benchmark manifest.


## HUMAN_GATE A — frozen decision
Approved by Product Owner before any SRPose38 anatomical result was observed.

Frozen policy version: `REFERENCE_EQUIVALENCE_V1`.

For LOT04 detector selection only:
- candidate landmark p95 error must not exceed the corresponding frozen LOT02 human p95;
- landmark median remains reported but is non-blocking for Option A; the schema field `max_median_mm` is therefore set equal to the same human p95 ceiling so it cannot introduce an unapproved stricter gate;
- candidate sentinel-measurement p95 absolute error must not exceed the corresponding frozen LOT02 G1-A human p95 absolute disagreement;
- no additive or multiplicative margin above the human envelope is authorized;
- unsupported identities remain non-passing and cannot be promoted by aliasing;
- overall PASS requires every required compatible landmark and sentinel measurement to PASS;
- missing, non-finite, or out-of-frame outputs are fail-closed and cannot be counted as PASS.

These are engineering reference-equivalence tolerances for LOT04 selection, not universal clinical-validity thresholds. Later human-review and clinical-validation gates remain mandatory.

The tolerance HUMAN_GATE is resolved. No post-result retuning is authorized.
