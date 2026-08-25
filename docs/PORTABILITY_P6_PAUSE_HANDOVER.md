# Portability P6 — Pause / Scientific Assets Refresh

Status: PAUSED, not closed, 0 EP credited.

## Goal P6
Produce a deterministic Windows installer with exact scientific runtime assets, frozen runtime self-test, install/upgrade/uninstall smoke, data preservation, and explicit signing status.

## Verified P6 state at pause
- Integration base: `portability/p10-update-engine`
- P6 PR: #242, OPEN/DRAFT
- Published P6 head: `90b1262cb13b22172d6d0d2f36aa6eb96d360cdf`
- Prepared but intentionally unpushed candidate object: `4501ad8d167c65a64e174d923e6f1d3a36b14399`
- Last dedicated P6 run: `32803814701` — FAILURE
- Static packaging contract: PASS
- Frontend production build: PASS
- Failure cause #1 fixed: requirements include path resolved as `backend/backend/requirements.txt`
- Failure cause #2 found: invalid global pin `protobuf==6.2.3`; prepared candidate pins `protobuf==5.29.6` and adds `pip check`
- No Vercel deployment.

## Scientific asset security
- `hraaaaf/Digital_crown` remains public during this work.
- Scientific weights must not be uploaded to this public repo or a public Release.
- Dedicated asset repo exists: `hraaaaf/DigitalCrown-assets`, verified PRIVATE and accessible by the connected GitHub app.

## Current runtime scientific contracts
### Cephalometry legacy
- Runtime: PyTorch `U_Net_w_Cartesian_SE`, 19 heatmaps, target 512x512.
- Expected weight path: `backend/ai_models/cephld_cca/ceph_weights.pth`.
- Source integration identifies the research family as `CephLD-CCA`.

### Cephalometry SOTA
- Runtime: ONNX Runtime, 38 heatmaps, target 1024x1024.
- Expected model name: `model.onnx`.
- Code states CL-Detection 38-point nomenclature.
- This SOTA model was already deferred from P5 to the separate Cephalometry NextGen benchmark; do not silently substitute a different model without scientific qualification.

### Panoramic
- Runtime: ONNX Runtime.
- Expected model: `backend/ai_models/panoramic_model.onnx`.
- Current parser assumes YOLO-style output, 1280x1280 input, classes exactly: `Caries`, `Deep Caries`, `Impacted`, `Periapical Lesion`.
- Current code labels inference mode `LOCAL_SOTA_YOLO11x`.

## Parenthesis workstream
Branch: `portability/p6-scientific-assets-refresh`

Goal: recover original GitHub weight sources where possible and evaluate lighter/more portable alternatives before resuming P6.

Success criteria:
1. Identify provenance for every weight used in P6, or explicitly mark provenance unresolved.
2. For each replacement candidate, record architecture/runtime, model size, required dependencies, Windows x64/macOS arm64 portability, license, downloadable weights, input/output contract, and scientific scope.
3. No candidate may replace a clinical model solely because it is smaller/faster.
4. Prefer ONNX Runtime CPU-compatible assets when scientific quality is equivalent or superior, because this avoids shipping the full PyTorch runtime.
5. Produce a recommended minimal asset set for P6 and a separate Cephalometry NextGen benchmark set.

## Exact resume sequence
Scientific-assets research -> choose/recover asset set -> store only in `hraaaaf/DigitalCrown-assets` private -> record SHA256/provenance/license -> update P6 manifest/workflow if needed -> move PR #242 to the fully prepared candidate -> one heavy Windows packaging run -> installer artifact + smoke + signing status -> P6 closeout only if all observable gates pass.
