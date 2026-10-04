# Cephalo vNext — LOT02 Aariz QC & SRPose38 Provenance Decision

Status: EXECUTABLE EVIDENCE — no clinical detector promotion
Date: 2026-10-02

## Goal
Resolve the two remaining public-Gold-Set ambiguities before LOT02 can use Aariz:
1. junior/senior annotation disagreement must never be averaged blindly;
2. the frozen SRPose38 checkpoint must have a reproducible published training lineage that does not include Aariz.

## Aariz source evidence
Official archive identity already frozen:
- DOI: 10.6084/m9.figshare.27986417.v1
- Figshare file: 51041642
- size: 2,098,209,792 bytes
- MD5: e0bd645bca6759abdae4f199d841bda6
- license: CC BY 4.0

Local materialization verified:
- 700 train / 150 valid / 150 test images;
- one Junior and one Senior annotation file for every case;
- 1000 per-image calibration rows;
- 29 landmarks per annotation.

The published Aariz workflow represents Junior and Senior annotation groups separately and derives the published reference from expert-reviewed annotations. Digital Crown does not treat that published averaging step as sufficient for every pair without QC.

## Deterministic QC policy
Executable implementation: scripts/classify_cephalo_vnext_lot02_aariz_qc.py

Triage only — 2 mm and 4 mm are NOT clinical acceptance limits:
- STRUCTURAL_INVALID: non-finite, non-positive, out-of-image coordinate, invalid image dimension, or invalid calibration.
- CONSENSUS_CANDIDATE: junior/senior disagreement <= 2.0 mm.
- REVIEW_REQUIRED: disagreement > 2.0 mm and <= 4.0 mm.
- ADJUDICATION_REQUIRED: disagreement > 4.0 mm.

Only CONSENSUS_CANDIDATE receives an automatic midpoint reference.
REVIEW_REQUIRED, ADJUDICATION_REQUIRED and STRUCTURAL_INVALID receive no automatic reference and cannot silently enter detector scoring.
All pairs remain in the QC output denominator. Hard cases are never dropped to inflate accuracy.

## Frozen SRPose38 provenance
Source repository: 5k5000/CLdetection2023
Frozen source commit: 18d17d1934970016e7610c4849311900b8d1f191

Published training recipe at that commit:
- input data requested from CL-Detection2023: train_stack.mha + train-gt.json;
- preprocessing creates 400 source cases and deterministic shuffled splits 300 train / 50 validation / 50 local test;
- model config uses the generated CL-Detection2023 train/valid/test JSON files;
- repository README states the published pretrained weight is trained on the combined train + validation CL-Detection datasets.

Published Google Drive model ID: 10HrNDBBpuECTcgNgcWNUt7kM6m4ZMXM4

Independent byte-level verification on the authorized Windows workstation:
- downloaded published file size: 268,846,952 bytes;
- downloaded SHA-256: fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc;
- this exactly equals the checkpoint SHA-256 already frozen in Digital Crown LOT04.

Repository search at the frozen source commit found no Aariz training/config/data reference.

### Provenance decision
PUBLISHED_RECIPE_NO_AARIZ_EXPOSURE_EVIDENCE

This is sufficient to classify Aariz as external evaluation material for the frozen published checkpoint under the declared source recipe. It does not claim proof about undisclosed author activity; it records reproducible provenance: exact published bytes + exact published training recipe + source search.

Any future fine-tuning, threshold tuning, alias tuning or checkpoint selection using Aariz invalidates untouched status for the affected subset and must create a new candidate identity.

## Gate impact
Aariz is eligible as external G2/reference evidence after deterministic QC. It is not by itself sufficient for CEPH_GOLDSET_READY: G3 Digital Crown compatibility fixtures and the final frozen acceptance subset/manifest still need executable proof.

No runtime/model/patient/master mutation is authorized by this decision.
