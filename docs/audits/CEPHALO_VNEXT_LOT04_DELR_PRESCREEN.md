# Cephalo vNext — LOT04 DeLR Candidate Prescreen

Status: PRE-BENCHMARK REJECTED — structural coverage mismatch
Gate target: `CEPH_DETECTOR_SELECTED`

## Candidate inspected
- Repository: Hugging Face dataset repo `emad2001/DeLR-Cephalometric-ConvNeXtV2`
- Frozen Hub revision: `47f4fc061bd8df7981295fe062853081b6e56ad6`
- Candidate checkpoint advertised: `checkpoints/Aariz_26/best_model.pt`
- Architecture: DeLR / ConvNeXtV2-tiny
- Aariz split declared by source: 700 train / 150 valid / 150 test
- Public source reports Aariz_26 performance around 1.073 mm MRE with 87.0% SDR@2mm.
- Checkpoint was **not downloaded** by Digital Crown during this prescreen.

## Structural coverage finding
The frozen source loader defines:
`LANDMARK_INDEX_26 = np.arange(26)`

The source explicitly documents this mode as retaining the first 26 Aariz landmarks and dropping:
- Soft Tissue Nasion;
- Soft Tissue Pogonion;
- Subnasale.

Under the existing LOT03/LOT04 anatomy-compatible Digital Crown acceptance set, the required 24 compatible landmarks include:
- `N_soft`;
- `Pog_soft`;
- `Sn_soft`.

Therefore the public `Aariz_26` checkpoint can cover at most **21/24** required compatible LOT04 landmarks.

## Gate consequence
`REFERENCE_EQUIVALENCE_V1` requires every required compatible landmark and every sentinel measurement to PASS for overall detector PASS.

A candidate missing three required landmarks cannot satisfy this predeclared gate without changing the contract after candidate selection.

Changing the acceptance set now to accommodate this checkpoint would be post-hoc gate relaxation and is forbidden.

## Untouched protection
No checkpoint download.
No Aariz inference.
No prediction artifact.
No acceptance record.
No threshold or split change.

The untouched acceptance protocol is therefore not consumed by this candidate.

## License / provenance note
The Hub README says to see/add a repository licence before publishing; a clear weight-specific licence was not established during prescreen.
This would also require resolution before any production redistribution, but the structural coverage mismatch already rejects the candidate for LOT04 selection.

## Alternative search outcome
Current public-candidate search also inspected:
- `Cestovatels/CephaloHRNet`: relevant HRNet implementation but no public trained checkpoint/release located.
- `manwaarkhd/CEPHMark-Net`: source available, but no checkpoint found in the frozen repository and no repository licence file located.
- 19-landmark public cephalometric checkpoints: insufficient coverage for the frozen 24-landmark LOT04 gate.

No currently inspected frozen public checkpoint covers the full required LOT04 compatible set with downloadable weights and sufficiently traceable semantics.

## Decision
DeLR `Aariz_26` is **REJECTED BEFORE BENCHMARK** for LOT04 detector selection due to structural landmark-coverage mismatch.

`CEPH_DETECTOR_SELECTED` remains **NOT SATISFIED**.

## Next exact
Do not consume the untouched set on another structurally incapable candidate.

Next viable paths:
1. obtain a frozen external checkpoint that covers all required compatible landmarks and verify its source/licence/preprocessing before Aariz inference; or
2. open a separate model-training lot for a full-coverage detector trained strictly on development data only, with training protocol/hyperparameters/model-selection rules frozen before any untouched test evaluation.

Training a new model is a new scope and must not reuse the untouched Aariz test split for tuning or checkpoint selection.
