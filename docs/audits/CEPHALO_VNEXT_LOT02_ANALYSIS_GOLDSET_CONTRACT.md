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

### G1 — Qualified public expert reference with explicit ambiguity track
G1 is split into two non-interchangeable tracks:
- **G1-A Consensus Gold** — exact landmark reference is permitted only when the two Aariz expert-group annotations are structurally valid and differ by <=2.0 mm after per-image calibration. The reference coordinate is their midpoint.
- **G1-B Ambiguity Stress Set** — pairs >2.0 mm, structurally invalid pairs, and all pairs requiring review/adjudication remain visible in reporting but are never silently averaged into exact ground truth.

The 2/4 mm bands are QC triage boundaries only, not clinical detector-acceptance thresholds. G1-B remains in denominators/coverage reporting to prevent easy-case selection bias. Performance summaries MUST disclose both G1-A exact-reference performance and G1-B unresolved/coverage behavior.

Immutable evidence record: `docs/audits/schemas/cephalo_vnext_lot02_aariz_qualification.json`.

### G2 — External generalization role
The same official Aariz source provides cross-device stratification across seven acquisition devices, but G2 is a distinct evaluation role from G1 reference qualification. Only anatomy-compatible mappings are allowed. Unsupported DC points are never coerced into Aariz labels. Train/valid/test membership remains frozen; final detector acceptance MUST NOT use any subset exposed during model or threshold tuning.

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

The previous missing-corpus blocker is resolved by material evidence:

- G0 executable synthetic geometry oracle now covers exact sentinel geometry and fail-closed degeneracy.

- Aariz official archive verified by exact size and MD5.
- 1000 cases frozen as 700 train / 150 valid / 150 test with paired Junior/Senior expert-group annotations.
- Manifest V2 records image SHA-256, dimensions, annotation SHA-256 and split membership; local frozen manifest SHA-256: `d7191e61ff3ddd58ee8598c9f98cce1b71d5ebc7151b2975534ee644175181ff`.
- 29,000 paired annotations were calibrated in mm and deterministically classified: 27,248 CONSENSUS_CANDIDATE; 1,309 REVIEW_REQUIRED; 441 ADJUDICATION_REQUIRED; 2 STRUCTURAL_INVALID.
- Sentinel measurement agreement is frozen for SNA, SNB, ANB, FMA, IMPA, FMIA, SN-GoGn, Co-A and Co-Gn across all 1000 cases; no computation failures.
- Aariz publication source-locks intra-observer repeatability evidence (DOI 10.1038/s41597-025-05542-3); executable DC evidence remains the downloaded Junior/Senior corpus.
- Ambiguous pairs are retained as G1-B stress evidence and cannot become exact ground truth without adjudication.
- G3 synthetic legacy fixture is present and executable; migration tests prove exact round-trip preservation and no silent historical recomputation.
- SRPose38 source checkpoint provenance is byte-identical to the published CLDetection2023 pretrained weight; the published training procedure consumes CLDetection2023 train_stack.mha/train-gt.json and contains no Aariz reference. This is provenance evidence, not a clinical performance claim.

Therefore `CEPH_GOLDSET_READY` is satisfied for the LOT02 gold-set contract itself: G0 executable geometry, G1-A exact consensus reference, G1-B ambiguity stress evidence, G2 cross-device role, and G3 executable legacy oracle are all materialized with explicit limitations. This gate does not select a detector or confer clinical validity. Detector selection and clinical acceptance remain separate LOT04/LOT09 concerns. LOT02 does not authorize SRPose38 clinically.
