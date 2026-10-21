# RICKETTS_MANDIBLE_SPECIALIST_V1 — CPU training POC

Status: **NON-CLINICAL TRAINING INFRASTRUCTURE ONLY**

## Goal

Provide a reproducible GitHub-hosted CPU pipeline for the future Ricketts mandibular specialist.

The model output contract is deliberately minimal:

1. `R1_Ricketts`
2. `R2_Ricketts`
3. `R3_Ricketts`
4. `R4_Ricketts`
5. `Pm_Ricketts`
6. `DC_Ricketts`

`Xi_Ricketts` is **not** a neural-network output in this design. It must be derived by the separately validated Ricketts R1-R4 geometric construction.

## Safety boundary

The CI smoke dataset is synthetic and exists only to prove that:

- PyTorch training runs on a standard GitHub-hosted CPU runner;
- the model can be exported to ONNX;
- ONNX Runtime reproduces the PyTorch output within a strict numerical tolerance;
- outputs and provenance can be packaged as immutable workflow artifacts.

The resulting smoke weights are marked `NON_CLINICAL_SMOKE_ONLY` and **must never be loaded by the Digital Crown clinical runtime**.

No clinical runtime file is modified by this POC.

## Real-data gate

Clinical training remains fail-closed.

A future real dataset must provide a manifest with:

- schema = `RICKETTS_MANDIBLE_SPECIALIST_DATASET_V1`;
- exact ordered landmarks listed above;
- `license_verified=true`;
- `clinician_annotation_verified=true`;
- patient-level train/validation/test split provenance;
- de-identification/privacy evidence;
- source image geometry/calibration metadata where applicable.

Passing the manifest gate still does not enable clinical training in this POC. That activation requires a separate reviewed change.

## Validation outputs

The workflow must persist:

- model ID and exact landmark order;
- seed and epoch count;
- train/validation sample counts;
- initial/final smoke loss;
- validation pixel MAE (smoke diagnostic only);
- PyTorch↔ONNX max absolute delta;
- ONNX SHA256;
- explicit `NON_CLINICAL_SMOKE_ONLY` marker.

No clinical accuracy claim can be derived from smoke metrics.
