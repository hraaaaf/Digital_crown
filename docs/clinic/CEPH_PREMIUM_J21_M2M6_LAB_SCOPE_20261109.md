# CEPH-PREMIUM-V1 — J2.1 M2-M6 — Parallel lab integration notes — 2026-11-09

**Scope:** isolated lab branch stacked on J2.1-M1 PR #1252. No merge, clinical route, patient data, DB migration, production or desktop installer.

## Execution split and gates
- M2: `backend/services/ceph_premium_pixel_transform_lab.py`: 8 EXIF orientations, source pixel→crop/fit/zoom/pan/viewport and exact inverse, crop boundary/NaN/finiteness refusal; two verified ANUG public radiograph render previews 1280×900 and 1600×1000, using genuine prior J1 SRPose38 landmark coordinates.
- M3: `backend/services/ceph_premium_scene_ledger_lab.py`: append-only revisions, optimistic compare-and-swap SHA and parent linkage, integrity-checked re-open, invalidate cached measurements after landmark/contour/calibration changes. Storage restricted to `:memory:` SQLite, NOT production DB.
- M4: `backend/services/ceph_premium_scene_source_lab.py`: fail-closed read-only adapter to DC-DOS-05 authenticated original verifier plus independent SHA and JPEG/PNG source pixel-size verification. Lab test passes a synthetic verified binding envelope; this is NOT real authenticated DC-DOS-05 FUE. A separate real JWT integration test was drafted but its Windows backend test startup hung without evidence; keep as HOLD, not PASS.
- M5: negative tests reject cross-tenant/patient/study, wrong original SHA/revision/asset, fake clinical flag, duplicate radio bindings, invalid image and image-size swap, stale CAS, scientific identity mutation and tampered persisted scene.
- M6: `scripts/ceph_premium_j21_m6_lab_preview.py` replays *prior J1 exact-HEAD genuine* ONNX points `source-locked-38-points.json` on the exact public ANUG original SHA `ede247cd...`. Generates actual raster overlays for two viewports and writes detached proof JSON. **This is NOT a screenshot or FUE of the Digital Crown Desktop application, and not a new ONNX inference. M6 remains HOLD.**

## Critical historical compatibility repair
The real J1 artifact `source-locked-38-points.json` contains 38 IDs + x/y but NO per-point confidence score. M1 originally required confidence for every auto point, which would have forced invented data. Modified schema now carries explicit `score_status=NOT_EMITTED` and `confidence=null` (or AVAILABLE+genuine numeric score) and tests now cover legitimate missing model scores.

## CI
`.github/workflows/ceph-premium-j21-m2m6-fue.yml` sets a true four-lane matrix for M2/M3/M4/M5, each independent with same HEAD; M6 lab integration depends on all four. M6 also re-runs M1-M5 contracts, restores genuine J1 ONNX coordinates from GitHub #42685230506 and downloads publicly licensed original ANUG with pinned SHA, then verifies raw scene & generated lab screenshots. No clinical release and no backend runtime registration.

## Lab proof scope
- 61 local M2-M5 unit+negative tests PASS after two test-harness corrections (epsilon rounding on pixel-edge inversion, invalid test constructor duplicated width kwarg). New J1 score missing status addressed in this branch; exact-HEAD CI must re-prove all 104 M1-M5 cases.
- Verified ANUG local public original JPEG SHA256 `ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6`, 399879 bytes.
- Reused prior J1 coordinate file 9577 bytes SHA256 `4c7c459ae0e612606ebdeba72752839d8718af834b50ab631e5cc98de818bdbe`, with J1 source/model hashes and 38 x/y.
- Local M6 lab preview generated PNG files; report explicitly says no new ONNX inference, synthetic media binding envelope and no Desktop UI FUE.

## HOLD
- No actual authenticated DC-DOS05 binding + real media bytes test completed on this exact branch.
- No T0/T1, no persisted patient DB, no clinical auto-contour model, no real Desktop scene save/re-open, no G5 approval, no PDF.
- No anatomy source-certified index 0..37 mapping, no mm calibration or orthodontist clinical validation.
- M2-M5 are LAB candidates. The checklist must not mark full missions GREEN unless their individual SUCCESS and PROOF (including Desktop/API where required) are met.

## Next exact
After exact-HEAD CI, independently inspect generated genuine ANUG lab overlays, fix CI if needed. Then implement connected Desktop scene FUE and authenticated DC-DOS05 source-link/ledger in an isolated FastAPI/JWT app and verify with the same source SHA. Only then close M2/M3/M4/M5 and eventually M6.
