# Cephalo vNext — LOT02 Analysis Coverage & Gold Set Contract

Status: CANDIDATE — documentation only
Parent: LOT01 candidate 8b722dd5686536997642ea07836bee6588de731a
Gate target: CEPH_GOLDSET_READY

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

G3 is a migration oracle, not a smoke test. Before LOT12, freeze representative legacy fixtures and expected outcomes for:
- persisted landmark coordinates and aliases;
- auto/manual/validated provenance and correction history;
- calibration values and physical-unit reconstruction;
- canonical and legacy measurement IDs/labels;
- NOT_COMPUTABLE/BLOCKED states;
- tracing geometry and visibility state;
- evidence/source graph;
- report/PDF semantic values and provenance;
- superimposition references and serial-study linkage.

Migration acceptance requires deterministic pre/post comparison. A record merely opening successfully is insufficient. Any intentional semantic change requires an explicit versioned migration rule, expected-difference fixture and rollback path. No silent recalculation of historical results is permitted.

## D. Required metrics
Landmarks: calibrated per-landmark Euclidean mm error, X/Y directional error, mean/median/SD/robust percentiles, SDR only as secondary predeclared summary, failure rate, device/quality stratification where available.

Clinical propagation: signed/absolute error for each angle/distance, reference-plane contribution, auto vs corrected vs reference, NOT_COMPUTABLE rate. A global MRE alone cannot certify an analysis.

Reproducibility: inter/intra-annotator agreement on a defined subset, repeatable calibration, versioned tolerance policy, exact model/checkpoint/preprocessing provenance.

Ground-truth qualification is mandatory before model scoring:
- at least two independent qualified annotators on the validation subset;
- adjudication rules declared before model comparison;
- inter-annotator landmark disagreement reported per landmark in calibrated mm and by X/Y direction;
- intra-annotator repeatability measured on a predeclared subset;
- measurement-level agreement reported for sentinel outputs (at minimum SNA, SNB, ANB, FMA/IMPA/FMIA, SN-GoGn, Co-A, Co-Gn and soft-tissue measures when enabled);
- AI acceptance cannot be materially tighter than the demonstrated uncertainty of its human reference without explicit justification.

## E. Acceptance policy
No universal 2 mm threshold is the sole clinical gate.

Landmarks are tiered:
- TIER_A_REFERENCE — reference-plane/construction, high downstream impact.
- TIER_B_MEASUREMENT — directly drives clinical measures.
- TIER_C_TRACING — mainly tracing/visualization.

Thresholds are declared and versioned **before looking at candidate-model benchmark results** and account for downstream sensitivity. A point may pass for tracing while remaining blocked for a sensitive measurement.

Tolerance policy is analysis-aware, not a single inherited 2 mm rule:
- landmark localisation thresholds are per-landmark/per-tier and calibrated in mm;
- angular and linear measurement tolerances are separately predeclared;
- systematic bias and limits of agreement are assessed, not only mean absolute error;
- thresholds must be justified from human-reference reproducibility plus downstream clinical sensitivity;
- no threshold is retrofitted to make a candidate detector pass;
- if evidence is insufficient to set a defensible clinical tolerance, the item remains RESEARCH_ONLY / BLOCKED rather than receiving an arbitrary number.

A measurement is promoted only if its landmark identities are locked, G0 geometry is exact, calibrated landmark + downstream errors are reported, failures are fail-closed, human correction exists, analysis/norm versions are explicit, and G3 compatibility passes before LOT12.

Validation datasets are separated from development/training data. Gold-set cases used for final acceptance must not be used to tune detector weights, preprocessing, thresholds or post-processing. Any exploratory exposure moves the affected cases out of the untouched acceptance subset and is recorded in the manifest.

## F. Normative safety
Geometric truth and normative truth are separate. LEGACY_UNVALIDATED remains untrusted for new claims. Aariz supplies no DC norms. Historical author values remain contextual until population/age/sex/scaling applicability is locked. Conflicts remain HOLD, never averaged.

## Gate
CEPH_GOLDSET_READY requires LOT01 locked, reviewed coverage, accepted G0-G3, reviewed metric/tolerance policy, a pre-registered ground-truth/adjudication protocol, and zero runtime/master mutation.

Before any benchmark run, a machine-readable validation manifest must freeze: case IDs/hashes, split membership, landmark-definition versions, analysis versions, calibration provenance, annotator roles, adjudication rule, metrics, tolerance-policy version, candidate model/checkpoint IDs and preprocessing version. Benchmark outputs must be write-once/versioned evidence and must never mutate this manifest.

This document authorizes no model training, patient export, runtime change, merge to master or deployment.

## Debt-zero gate decision

The repository inspection performed before LOT06 found no frozen executable G1 internal corpus and no frozen representative G3 legacy corpus satisfying this contract. Therefore `CEPH_GOLDSET_READY` is explicitly **NOT SATISFIED** at this revision. This is a hard evidence blocker, not accepted technical debt and not a documentation waiver.

Consequences:
- no detector may be clinically selected from LOT02 evidence;
- no anatomical-accuracy claim may be inherited from runtime parity;
- LOT06 engine geometry may proceed only with G0/manual deterministic landmark fixtures and MUST remain detector-independent;
- chain-level Cephalo 2.0 certification remains blocked until G1/G3 are materially created, independently reviewed and frozen.

Required unblock proof: immutable G1/G3 case manifests/fixtures, qualified annotator/adjudication provenance where applicable, preregistered tolerances derived from human-reference reproducibility, and executable deterministic comparison evidence.
