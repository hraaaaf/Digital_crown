# Cephalo vNext — LOT04 Detector Selection Execution

Status: OPEN — PRE-REGISTERED EXECUTION PREP; detector not selected
Gate target: `CEPH_DETECTOR_SELECTED`
Base evidence HEAD: `41b86a461142f7d9e8db1f74e61db778719eb2ae`

## Goal
Execute the frozen SRPose38 candidate against the qualified LOT02 Aariz reference without leakage, post-hoc threshold tuning, semantic substitution, or runtime mutation.

## Frozen candidate
- Model: `srpose38-tta-1024.onnx`
- ONNX SHA-256: `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`
- ONNX size: 267,484,931 bytes
- Checkpoint SHA-256: `fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc`
- Source commit: `18d17d1934970016e7610c4849311900b8d1f191`
- Provider: CPUExecutionProvider
- Output count: 38
- Preprocessing/decoder: frozen by LOT04 contract and runtime implementation.

## Qualified reference
LOT02 is closed as `CEPH_GOLDSET_READY`.
Aariz source: 1000 cases; 700/150/150 split; 29 landmarks; seven devices.
G1-A exact reference is restricted to qualified consensus pairs. G1-B unresolved pairs remain visible and are never silently averaged.
Aariz validates only anatomy-compatible mappings; unsupported SRPose38 identities remain BLOCKED / VALIDATION_REQUIRED.

## Contamination / untouched policy
The published frozen SRPose38 checkpoint provenance points to CL-Detection2023 training and no Aariz reference was found in the frozen source repository.
This supports Aariz as external evaluation material for the frozen published checkpoint, but does not prove absence of undisclosed author activity.
Any Digital Crown use of Aariz for tuning preprocessing, mapping, thresholds, checkpoint selection or post-processing would invalidate untouched status for the affected subset.

## Required execution artifacts
1. Concrete `CEPHALO_LOT04_BENCHMARK_MANIFEST_V1` generated before scoring.
2. Captured ONNX runtime interface and exact resolved dependency versions.
3. Immutable acceptance subset IDs/hashes.
4. Candidate predictions on the untouched subset.
5. Per-landmark calibrated mm + signed X/Y + failure metrics.
6. Seven-device stratification where sample size permits.
7. G1-B unresolved/coverage behavior.
8. Downstream sentinel measurement errors: SNA, SNB, ANB, FMA, IMPA, FMIA, SN-GoGn, Co-A, Co-Gn.
9. `CEPHALO_LOT04_ACCEPTANCE_RECORD_V1` cryptographically bound to the manifest and candidate hash.
10. Two adversarial reviews from zero + additional confirmation pass on one unchanged final HEAD.

## Human-reference baselines already frozen
Examples showing why no universal 2 mm gate is acceptable:
- S p95 human disagreement: ~0.457 mm.
- Go p95: ~4.142 mm.
- Po p95: ~4.342 mm.
- Or p95: ~3.455 mm.
- UIA p95: ~3.700 mm.
Sentinel G1-A human disagreement also varies materially: SNA p95 ~1.476°, FMA ~2.246°, IMPA ~3.734°, FMIA ~3.965°.

## Tolerance preregistration gate
**HUMAN_GATE A APPROVED before model scoring.**

Frozen policy: `REFERENCE_EQUIVALENCE_V1`, materialized in:
- `docs/audits/CEPHALO_VNEXT_LOT04_TOLERANCE_POLICY_HUMAN_GATE.md`;
- `docs/audits/schemas/cephalo_vnext_lot04_tolerance_policy_reference_equivalence_v1.json`.

Selection semantics are engineering reference-equivalence only, not universal clinical validity:
- candidate landmark median and p95 must not exceed the corresponding frozen LOT02 human median and p95;
- sentinel-measurement p95 absolute error must not exceed the corresponding frozen LOT02 G1-A human p95;
- no extra non-inferiority margin is authorized;
- missing/non-finite/out-of-frame outputs are fail-closed and cannot PASS;
- every required compatible endpoint must PASS for an overall PASS;
- unsupported identities remain blocked/validation-required.

No post-result threshold retuning is authorized.

## Current execution state
The qualified 2.1 GB Aariz corpus is materialized on authorized workstation `DESKTOP-3MAJEEH`.
The workstation was re-observed online after HUMAN_GATE A approval.
Before any scoring, corpus identity and frozen model bytes must be re-verified and an immutable manifest must be generated. No real candidate inference has yet been executed in this lot.

## Stop conditions
- Do not invent an acceptance result.
- Do not retune on the untouched subset.
- Do not reinterpret unsupported landmark identities.
- Do not call runtime parity anatomical validity.
- Do not select SRPose38 solely because it is the existing engineering baseline.
- No runtime/model/schema/patient/master mutation.
- No merge or deployment without explicit authorization.

## Next exact
1. Re-verify frozen model bytes and exact execution environment.
2. Generate immutable benchmark manifest from the verified corpus/candidate environment with `REFERENCE_EQUIVALENCE_V1`.
3. Execute SRPose38 inference once on the untouched acceptance subset.
4. Produce acceptance record and run semantic validator.
5. Review from biometrics/leakage and reproducibility/clinical-safety perspectives.
6. Confirm on same HEAD; grant `CEPH_DETECTOR_SELECTED` only if evidence passes.
