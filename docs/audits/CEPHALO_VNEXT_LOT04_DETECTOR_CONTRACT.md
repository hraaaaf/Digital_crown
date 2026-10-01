# Cephalo vNext — LOT04 Detector Contract & Benchmark Plan

Status: APPROVED — benchmark/protocol contract only
Parent: LOT03 ontology HEAD 8e97c8a7e7650f1b6807a9638d03dac76f69c267
Gate target: CEPH_DETECTOR_CONTRACT_APPROVED

## Goal
Freeze what the detector is, what its 38 outputs mean operationally, and how a future candidate is benchmarked without confusing runtime parity with anatomical/clinical accuracy.

## Frozen current candidate
- family: SRPose38 / CL-Detection-derived runtime
- source commit: 18d17d1934970016e7610c4849311900b8d1f191
- challenge source commit: dc1ce2bd0a3f317de4160cde17e4a6f60371e67c
- checkpoint SHA-256: fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc
- ONNX SHA-256: a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb
- ONNX size: 267484931 bytes
- pipeline evidence version: SRPOSE38_TTA_1024_V1
- output cardinality: exactly 38 channels
- current parity fixture image shape: 2400×1935×3
- runtime parity tolerance: 0.02 px
- previously certified ONNX/reference max delta: 0.0001999200562387517 px

These values prove artifact/runtime identity and numerical parity only. They do not prove anatomical accuracy.

## Output identity contract
Channel order is frozen to the LOT00/LOT03 SRPose38 mapping. A channel name is an operational model output, not automatically a clinically canonical anatomical identity.

LOT03 dispositions apply:
- clinically canonical identities require source-backed anatomy + benchmark validation;
- U6/L6 remain L3_RESEARCH_LEGACY_MOLAR because "Upper/Lower Molar" does not prove a source-specific cusp;
- generic Gn/Go/Po cannot silently acquire analysis-specific definitions;
- hard/soft tissue identities remain distinct;
- Occ_Ant/Occ_Post are outside the 38 detector outputs.

A future detector may have a different output set only under a new versioned contract and migration/benchmark decision.

## Preprocessing contract to freeze before benchmark
The executable benchmark manifest must hash/version:
1. input decode library/version and color-space convention;
2. orientation policy and rejection of ambiguous orientation;
3. resize/pad/crop geometry and interpolation;
4. normalization and dtype;
5. TTA transforms and inverse-coordinate mapping;
6. model input dimensions;
7. output decoder/post-processing;
8. coordinate convention (origin, axes, pixel center/edge convention);
9. mapping from output index to operational ID;
10. calibration provenance for conversion from px to mm.

No benchmark is valid if any of these are inferred after seeing acceptance results.

## Benchmark layers
### G0 — deterministic geometry/runtime
Purpose: prove transforms, inverse transforms, channel ordering, decoder, degeneracy/fail-closed behavior, and ONNX/reference parity.
No claim of anatomical accuracy.

### G1 — internal human-reference lateral set
Uses the LOT02 qualified reference contract:
- ≥2 independent qualified annotators on validation subset;
- adjudication declared before candidate results;
- inter-annotator disagreement per landmark in mm and X/Y;
- intra-annotator repeatability subset;
- calibration/device/image-quality metadata;
- immutable case hashes and untouched final acceptance subset.

### G2 — Aariz external generalization
Use only anatomically compatible mappings from LOT03.
Purpose: external/device/generalization evidence, not normative validation.
Aariz cannot validate SRPose-only identities and cannot authorize semantic aliases such as UMT/LMT↔U6/L6.

### G3 — legacy compatibility
Detector promotion must not silently reinterpret stored IDs, coordinates, corrections or historical reports. G3 remains the migration oracle defined in LOT02/LOT03 and is executed before integration, not waived by good G1/G2 scores.

## Leakage prohibition
Before candidate scoring, freeze a machine-readable manifest containing:
- case IDs + immutable hashes;
- split membership;
- exposed development vs untouched acceptance cases;
- landmark-definition versions;
- annotator/adjudication versions;
- model/checkpoint/ONNX hashes;
- complete preprocessing/decoder version;
- metric implementation version;
- tolerance policy.

Acceptance cases cannot tune architecture, checkpoint selection, preprocessing, decoder, thresholds, post-processing or landmark definitions. Any such change creates a new candidate and requires a fresh untouched acceptance evaluation.

## Required metrics
Report per landmark and stratified where sample size permits:
- Euclidean error in calibrated mm;
- signed X and Y error;
- mean, median, SD and robust percentiles;
- SDR as secondary reporting at predeclared distances, never as sole gate;
- missing/non-finite/fail-closed rate;
- device/source and image-quality strata;
- auto vs corrected vs adjudicated reference.

Also propagate landmark errors to sentinel clinical outputs from LOT02:
SNA, SNB, ANB, FMA, IMPA, FMIA, SN-GoGn, Co-A, Co-Gn and enabled soft-tissue measures.
Report signed and absolute measurement error and systematic bias / limits of agreement where appropriate.

## Acceptance policy
There is no universal "≤2 mm = clinically valid" gate.

Before seeing final candidate results, each promoted landmark gets a tier and preregistered tolerance justified by:
- demonstrated human-reference reproducibility;
- anatomical ambiguity;
- downstream measurement sensitivity;
- intended clinical consumer.

Thresholds for linear and angular downstream measures are separate.
A candidate cannot receive a tolerance materially tighter than the demonstrated human-reference uncertainty without explicit justification.
If evidence is insufficient, status is RESEARCH_ONLY, VALIDATION_REQUIRED or BLOCKED — never silently promoted.

## Human review / fail-closed
Automatic output remains reviewable and correctable.
Missing, non-finite, out-of-frame, low-integrity or semantically unvalidated outputs cannot be used to fabricate a clinical measurement.
Manual correction creates new evidence/provenance; it does not rewrite the original auto evidence.
Final clinical use remains subject to the later Human Review/Validation lots.

## Candidate comparison
A replacement detector is compared against:
1. qualified human reference;
2. current frozen SRPose38 candidate;
3. human-reference variability.

"Better MRE" alone cannot win. Promotion requires no clinically important regression in high-impact landmarks/measurements and acceptable failure behavior. Aggregate improvements cannot hide a dangerous landmark-specific regression.

## Evidence boundary
Existing SRPose38 runtime parity proves reproducibility of the frozen artifact:
- exact model hashes;
- exact 38-output contract;
- strict runtime coordinate parity on the certified fixture;
- evidence graph enforces exact 38 IDs for automatic evidence.

It is a baseline engineering proof, not the LOT04 anatomical benchmark.

## Gate
CEPH_DETECTOR_CONTRACT_APPROVED requires:
- detector artifact/output/preprocessing contract frozen;
- benchmark layers and leakage rules frozen;
- metrics and acceptance methodology frozen before candidate results;
- fail-closed/human-correction semantics explicit;
- LOT03 ontology dispositions preserved.

It does not require the future G1/G2 benchmark to already pass. Actual detector-performance certification belongs to the later validation execution gate.

No runtime/model/schema/patient/master mutation is authorized by this document.


## Adversarial review record

### Double-check — internal independent perspective 1: biometric validation / leakage
Prompt: "Assume LOT04 will overstate detector quality. Find leakage, threshold tuning after results, misuse of 2 mm, aggregate metrics hiding landmark failures, calibration errors, weak human reference, device-domain bias, and failure to propagate landmark error into clinical measurements. Return blockers/major/minor findings and a severe /10 score."

Result: no blocking finding in the contract. The plan freezes untouched acceptance data and the complete candidate/metric/tolerance manifest before scoring; uses calibrated per-landmark and directional metrics; treats SDR as secondary; requires human-reference reproducibility and downstream measurement propagation; and prohibits a universal 2 mm clinical gate.
Severe score: **9.2/10**.
Residual: actual G1 sample composition, sample-size justification and quantitative tier tolerances cannot be scored until the corpus and human reproducibility data exist.

### Triple-check — internal independent perspective 2: reproducibility / clinical safety
Prompt: "Try to make a numerically reproducible detector unsafe in production. Look for artifact drift, preprocessing drift, channel reorder, semantic aliasing, non-finite/out-of-frame outputs, silent correction overwrite, historical reinterpretation, and a replacement model that wins aggregate MRE while regressing a clinically critical landmark. Return blockers/major/minor findings and a severe /10 score."

Result: no blocking finding. Hashes/output cardinality are frozen; preprocessing/decoder must be versioned before benchmark; LOT03 semantic HOLDs survive; automatic evidence is immutable relative to corrections; failure states are fail-closed; candidate comparison prohibits aggregate gains from hiding clinically important regressions.
Severe score: **9.3/10**.
Residual: the preprocessing implementation is not yet fully enumerated from executable code in this documentation lot; exact implementation freeze must be generated/verified before running G1/G2.

## Gate decision
**CEPH_DETECTOR_CONTRACT_APPROVED** for the benchmark/protocol contract only.

This approval freezes how detector candidates must be identified and evaluated. It does not certify SRPose38 anatomical performance, does not claim G1/G2 passed, and does not authorize model/runtime/master mutation.
