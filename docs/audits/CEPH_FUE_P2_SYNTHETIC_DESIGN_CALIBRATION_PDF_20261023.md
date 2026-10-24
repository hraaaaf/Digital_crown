# CEPH FUE-P2 — true browser, **digitally constructed** phantom ruler → draft PDF

**2026-10-23; DRAFT; GitHub Actions disposable T2 only; clinical NO-GO.**

## Intent

Continuation of [FUE-P1 #1043](https://github.com/hraaaaf/Digital_crown/pull/1043), whose exact HEAD `be2a4464ba11a97b0d3325b15de24ee930683d45` had green 6/6 real P1 checks, after FUE-H 6/6. User authorized running P2.

An authentic **manual two-point calibration workflow** needs known geometry. We do NOT invent physical mm on a real person's radiograph. Instead `scripts/ceph_fue_p2_generate_phantom.py` creates a **completely nonhuman**, deterministic 1024×1024 image with manufactured digital ruler marks at (420,500) and (620,500). The distance is **200 digital pixels = 20 design mm**, or 0.1 **design mm/px**, exactly by construction. This is NOT the true physical scale of any anatomy, NOT clinical ground truth, and is absolutely NOT a validation of cephalometric measurements.

## Actual end-to-end browser scenario

1. Prerequisites: genuine FUE-H (isolated FastAPI+JWT+React+Chromium, public authentic cephalograms, true 38 ONNX inference, protected media/tenant security) and FUE-P1 (correction/undo/save, uncalibrated blocker), both rerun exact HEAD.
2. Generate and hash the pure synthetic phantom; obtain **fresh authenticated Cabinet browser** session, upload it through the actual React file-input widget, verify real ONNX returns 38 (regardless of their anatomical meaning) and a NEW DB study is persisted.
3. Click **two real pixels in the browser on the manufactured ruler**, enter 20 **synthetic design-mm**, submit actual POST calibrated route. Backend must persist correct ratio near 0.1 and `calibration_data.method=MANUAL_TWO_POINT` with audited points and distance. Fail closed for any mismatch.
4. **Actual user StepTab 2 (Moulages), StepTab 3 (Synthèse clinique), StepTab 4 (Documents & stratégie)** after the synthetic calibration. No shortcuts, store mutations or invented patient imaging calibration.
5. Through actual Document UI, click **Brouillon PDF**, capture actual PDF HTTP bytes and browser download, verify binding to selected `analysis_id` and `expected_revision` by roundtrip response headers, and forbid archive. Exercise **Prévisualiser** under the same source-binding rules. Generated synthetic draft is test evidence only.
6. Output only synthetic images, known test study ID, aggregate report and draft PDF under transient GitHub Actions artifact (30 days). No private patients, no secrets, no external vendor, no Production.

## Safety and expected outcomes

Even if every browser step and actual PDF succeeds: **FUE-P2 functional test passes only on synthetic design geometry**; `CEPH_DETECTOR_SELECTED=NO`, **CLINICAL NO-GO**, six Ricketts source HOLDs, SRPose38 experimental accepted-error only. The fake phantom does NOT authorize applying 0.1mm/px to any patient, nor claiming clinical correctness, nor authorizing any official archived treatment plan. `facad_parity_verified=false`; no vendor FACAD action or D3 exposure.

Source CI is strictly fail-closed: any failure in real model, calibration route/provenance, StepTab transitions, PDF byte stream, selected study identity/revision, or synthetic/clinical boundary is RED. A green workflow still does **not** close a top-level clinical checklist item.

**Roadmap remains 41/99** (CEPH 20/60 and FAC 21/39) until exact canonical acceptance criteria are individually satisfied and checked. PR DRAFT, no merge/deploy/production change.

## Review dependencies

- Source fidelity: preserve exact parent PR #1043, no modifications to product or calibration rules.
- Science: phantom design-calibration evidence is NOT a medical reference; no landmark ground truth.
- Security: no raw patient data, no fake auth; previous tenant guards must rerun.
- UX: avoid claiming visual human approval based solely on screenshots.
