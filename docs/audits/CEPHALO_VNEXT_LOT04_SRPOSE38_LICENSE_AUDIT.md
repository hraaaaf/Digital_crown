# Cephalo vNext — LOT04 SRPose38 License Audit

Status: OPEN — WEIGHT_LICENSE_EXPLICITNESS_UNRESOLVED
Gate target: `CEPH_DETECTOR_SELECTED`
Source repository: `5k5000/CLdetection2023`
Frozen source commit: `18d17d1934970016e7610c4849311900b8d1f191`

## Verified
- The frozen source repository contains a `LICENSE` file at the exact source commit.
- That repository license is **Apache License 2.0**.
- The same frozen README links a pretrained SRPose checkpoint hosted externally on Google Drive and describes it as a model pretrained on combined train + validation data.
- The Digital Crown frozen checkpoint SHA-256 is `fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc`.

## Limitation
The pretrained weight is not stored as a repository file at the frozen commit, and the README does not state a separate checkpoint/model-weight license or explicitly say that the repository Apache-2.0 license applies to the externally hosted weight.

Therefore this audit does **not** infer commercial redistribution/product rights for the checkpoint from the code license alone.

## Gate effect
- Local reproducibility/benchmark execution may proceed; this audit does not alter or tune the candidate.
- Final `CEPH_DETECTOR_SELECTED` must not be represented as clearing product redistribution/commercial licensing while weight-license explicitness remains unresolved.
- Before production integration/redistribution, obtain a source-backed weight-license statement or explicit permission covering the exact checkpoint/model distribution.

## Evidence
- Source `LICENSE` at frozen commit: Apache License 2.0.
- Source `README.md` at frozen commit: pretrained weight distributed by external Google Drive link; no separate weight-license statement observed.
