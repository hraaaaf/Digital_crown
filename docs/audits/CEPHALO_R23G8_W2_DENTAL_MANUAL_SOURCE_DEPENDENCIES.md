# CEPH-UXCLIN-01 · R23-G8-W2 — Ricketts Atlas33 dental and manual source dependencies

**Date:** 2026-10-17. **Product:** Digital Crown cephalometry on DESKTOP ONLY. **Status:** source-requirement publication, not clinical authorization. PR #911 remains DRAFT.

## Canonical scope: seven source-locked but conditional factors

The canonical backend already implements these seven conditional methods in `backend/services/cephalo_canonical_analysis_v2.py`. Atlas2009 chapter 13 distinguishes these definitions from generic dental points; only `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1` may use this W2 source-obligation preview. These descriptions do not assert whether the active patient's source-image evidence exists or is anatomically correct.

| Atlas row | Canonical factor | Exact DIRECT landmarks | Required constructions | Manual and calibrated gates |
|---|---|---|---|---|
| #1 Molar relationship | `M_RICKETTS_MOLAR_RELATION_FOP_MM_V1` | `L6_DISTAL_Ricketts`, `U6_DISTAL_Ricketts` | Ricketts functional occlusal plane **FOP** | Both distal landmarks manual/manual-corrected, verified mm calibration; no tooth-center substitutions |
| #2 Canine relationship | `M_RICKETTS_CANINE_RELATION_FOP_MM_V1` | `L3_CUSP_Ricketts`, `U3_CUSP_Ricketts` | Ricketts FOP | Both cusp landmarks manually sourced, verified mm calibration |
| #3 Overjet projected onto FOP | `M_RICKETTS_OVERJET_FOP_MM_V1` | `L1_incisal`, `U1_incisal` | Ricketts FOP | Verified mm calibration, Ricketts sign; NOT generic overjet |
| #5 Lower-incisor occlusal extrusion | `M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1` | `L1_incisal`, `L1_apex` | Ricketts FOP | Explicit L1 long axis and FOP, verified mm calibration |
| #9 Upper molar relative to PTV | `M_U6_PTV_MM_V1` | `U6_DISTAL_Ricketts` | Ricketts PTV from manual `PR_Ricketts_PTV` and anatomical Frankfort | Manual U6 distal AND manual upstream PR via PTV construction, verified mm calibration |
| #15 Occlusal-plane inclination to Xi→Pm | `M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1` | `Pm_Ricketts` | Ricketts FOP and Xi ramal rectangle | Manual Pm AND manual upstream R1/R2/R3/R4 via Xi construction, angular, no mm calibration |
| #17 Upper-lip length | `M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1` | `ANS`, `LABIAL_COMMISSURE_Ricketts` | None | Explicit manual Ricketts commissure (NOT Stomion), same image, verified mm calibration |

**Every factor additionally requires SAME `source_image_ref` for its direct landmarks and the exact canonical constructions**, current provenance, availability statuses, and calibration if declared. Constructed FOP (premolar→molar directional plane) must come from its source-specific landmarks; neither a generic occlusal line nor an inferred tooth label is accepted. PTV and Xi have their own manual upstream landmarks which W2 lists as **indirect** construction obligations, not direct measurement landmarks. This avoids false assertions when only the direct IDs appear in the UI.

## Deliverables and evidence

- `docs/audits/schemas/cephalo_r23g8_w2_atlas33_dental_manual_dependencies_v1.json`: 7 exact factor identifiers / method names, direct landmarks, source construction definition IDs, manual flags, indirect manual upstream landmarks, calibration gates, Atlas exact gate and source references.
- `frontend/src/features/ortho/cephaloR23G8W2DentalRequirements.ts`: Atlas-only **READ-ONLY** dependency preview, no computation, no source image metadata inference, no SVG Focus.
- `CephaloR23G2ProtocolPanel.tsx`: on selecting one W2 row, labels missing direct points, manual origin and indirect manual construction obligations. Switching away to Gregoret clears the preview. **It does not assert that any selected anatomy or calibration was verified.**
- `scripts/cephalo_r23g8_w2_dental_coverage.py`: validates original Atlas 33 orders and gates, existing 8 LOT06 +3 G7 +4 W1, W2 exact canonical backend methods and manual/same-image checks, and 7 source obligations; any drift or aliases fail closed.
- Test suites: Python identity/alias/method/overlap/authority tests and Vitest/React source-only tests. GitHub CI on exact PR SHA uploads a source dependency ledger.

**Expected ledger:** 8 LOT06 +3 G7 +4 W1 +7 W2 = 22 published dependency descriptions; **11 W3 craniomandibular source Focus obligations remain unpublished**. These are not counts of clinically validated measurements.

## Safety and clinical NO-GO

Do not infer patient-source correctness or manual clinician validation from `presentLandmarkIds` alone; these are names supplied to the preview. A numeric result must pass the existing typed active measurement and provenance/calibration gates; an SVG Focus must additionally be authorized by row-specific active runtime `focus_evidence`. W2 **does not add or change those authority paths**. It does not expose normative or orthodontic diagnostic assessments. Test geometry on synthetic public radiographs is not a clinical gold standard.

Independent orthodontist/radiologist clinical evaluation of direct/indirect manual points, calibration, same-image provenance, FOP sign and dental repeatability remains necessary before patient-facing clinical approval. No merge or deployment in this lot.
