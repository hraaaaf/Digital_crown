# Cephalo vNext — LOT02 Analysis Coverage & Gold Set Contract

Status: CANDIDATE — documentation only
Parent: LOT01 candidate 8b722dd5686536997642ea07836bee6588de731a
Gate target: CEPH_GOLDSET_CONTRACT_LOCKED

## Goal
Define exactly what Cephalo 2.0 must prove before detector/schema implementation: analysis coverage, blocked dependencies, and a reproducible gold-set protocol.

## A. Coverage matrix
| Analysis/version | Already covered | Gap | Hard block |
|---|---|---|---|
| Steiner 1953 | SNA, SNB, ANB, U1-NA°, L1-NB°, interincisal, SN-GoGn | occlusal-SN; L1-GoGn | facial crown surfaces; exact molar points |
| Steiner 1959 | none promoted | Pog-NB; serial module | D identity; facial crown surface |
| DC Tweed Po-Or | FMA, IMPA, FMIA geometries | profile/read-path completeness | detector anatomical identity |
| McNamara 1984 | SNA, Co-A, Co-Gn, ANS-Me | A/Pog-Nperp, differential, MP/facial-axis | PTM identity; crown surfaces; airway |
| Ricketts 1981 lateral | facial-angle geometry, facial-axis geometry, convexity, interincisal, Li-Eplane | palatal plane; strict MP; bend | Pt identity; Xi/Pm; strict U6/PTV |
| Ricketts 1981 frontal | none | none authorized | BLOCKED_MODALITY_PA |
| COM/CRANIOM | most legacy geometry | overjet/overbite provenance | detector identity + legacy norms |

## B. Non-substitution contract
Gold-set cases must distinguish Pt_Ricketts vs PTM_McNamara; Gn_anatomic vs Gn_constructed; Pog_hard vs Pog_soft; Go-Me vs Go-Gn vs Ricketts Sub.Go.-M; generic/cusp U6 vs Ricketts distal crown; incisal edge vs facial crown surface; DC Tweed Po-Or vs strict historical ear-rod construction; Ricketts Facial Angle vs legacy FACIAL_DEPTH label; McNamara Pog-Nperp vs Situation_B.

Accidental equality in one image is never semantic equivalence.

## C. Gold-set layers
### G0 — Synthetic geometry truth
Exact fixed-coordinate expected values, sign/orientation, degeneracy and fail-closed cases, aliases and non-substitution tests.

### G1 — Internal manually reviewed lateral set
Representative image quality, dentition and difficult landmarks (Po, Co, Go, PNS, Ar/Ba/PT region), dental/soft-tissue visibility and calibration conditions. Each case stores immutable image hash, device metadata when known, calibration provenance, versioned landmark definitions, annotator/reviewer provenance, correction history, analysis version and expected measurements/tolerances.

### G2 — Aariz external generalization
Use official Aariz split/device metadata only for anatomically compatible mappings. Purpose = cross-device landmark validation, not Digital Crown normative validation. Unsupported DC points are never coerced into Aariz labels.

### G3 — Legacy compatibility
Representative existing DC schema, manual corrections, calibration, evidence graph, tracing, PDF/report and superimposition states. Use de-identified/synthetic material according to test policy.

## D. Required metrics
Landmarks: calibrated per-landmark Euclidean mm error, X/Y directional error, mean/median/SD/robust percentiles, SDR only as secondary predeclared summary, failure rate, device/quality stratification where available.

Clinical propagation: signed/absolute error for each angle/distance, reference-plane contribution, auto vs corrected vs reference, NOT_COMPUTABLE rate. A global MRE alone cannot certify an analysis.

Reproducibility: inter/intra-annotator agreement on a defined subset, repeatable calibration, versioned tolerance policy, exact model/checkpoint/preprocessing provenance.

## E. Acceptance policy
No universal 2 mm threshold is the sole clinical gate.

Landmarks are tiered:
- TIER_A_REFERENCE — reference-plane/construction, high downstream impact.
- TIER_B_MEASUREMENT — directly drives clinical measures.
- TIER_C_TRACING — mainly tracing/visualization.

Thresholds are declared before benchmark execution and account for downstream sensitivity. A point may pass for tracing while remaining blocked for a sensitive measurement.

A measurement is promoted only if its landmark identities are locked, G0 geometry is exact, calibrated landmark + downstream errors are reported, failures are fail-closed, human correction exists, analysis/norm versions are explicit, and G3 compatibility passes before LOT12.

## F. Normative safety
Geometric truth and normative truth are separate. LEGACY_UNVALIDATED remains untrusted for new claims. Aariz supplies no DC norms. Historical author values remain contextual until population/age/sex/scaling applicability is locked. Conflicts remain HOLD, never averaged.

## Gate
CEPH_GOLDSET_CONTRACT_LOCKED requires LOT01 locked, reviewed coverage, accepted G0-G3, reviewed metric/tolerance policy and zero runtime/master mutation.

This document authorizes no model training, patient export, runtime change, merge to master or deployment.
