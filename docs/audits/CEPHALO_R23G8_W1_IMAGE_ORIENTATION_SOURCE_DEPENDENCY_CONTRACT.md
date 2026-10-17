# CEPH-UXCLIN-01 — R23-G8-W1 — Atlas2009 signed orientation requirements (desktop-only)

**Status:** SOURCE OBLIGATIONS ONLY / NO CLINICAL RELEASE. Date 2026-10-17.

## What W1 actually resolves

Earlier LOT08 contracts have already defined the four signed geometry methods, the Pydantic `ImageOrientationEvidence` model, source-image matching, graph provenance checks and the runtime’s conditional calculation. W1 **does not invent or activate** a new orientation convention. It publishes their **exact, source-backed requirements** for the Atlas2009 table and creates a reproducible ledger.

Original source lock: `docs/audits/CEPHALO_LOT08_IMAGE_ORIENTATION_EVIDENCE_CONTRACT.md`, `docs/audits/CEPHALO_LOT08_RICKETTS_ATLAS33_WAVE_D_SOURCE_LOCK.md`; Atlas protocol `backend/data/cephalometry/ricketts_atlas2009_complete33_protocol_profile_v1.json`, source implementation `backend/services/cephalo_canonical_analysis_v2.py`.

| # | Signed Atlas factor | Exact direct landmarks | Required source constructions | Calibration |
|---|---|---|---|---|
| 4 | Overbite `M_RICKETTS_OVERBITE_FOP_MM_V1` | `U1_incisal`, `L1_incisal` | `RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1` | verified mm required |
| 14 | FOP→Xi `M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1` | none direct (constructed) | `RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1`, `RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1` | verified mm required |
| 18 | Commissure→FOP `M_RICKETTS_COMMISSURE_FOP_MM_V1` | `LABIAL_COMMISSURE_Ricketts` (manual/manual-corrected) | `RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1` | verified mm required |
| 24 | Palatal plane→FH `M_RICKETTS_PALATAL_PLANE_FH_DEG_V1` | `Po_anatomic`, `Or`, `ANS`, `PNS_Ricketts` (manual/manual-corrected) | none direct | angular, no mm calibration |

**Every row additionally requires** an evidence-graph-linked `ImageOrientationEvidence` corresponding to the exact same `source_image_ref`, finite/nondegenerate orthogonal **anterior and superior** anatomical axes, explicit `is_mirrored`, validated `provenance_ref` + `evidence_refs`. Origin `MANUAL_VERIFIED` requires `validated_by` and `validated_at` and appropriate graph validation. The model is **not proof of the orientation actually being correct in a real patient image**. The frontend may not infer these values from screen X/Y, flip the image to make a sign plausible, or assert a validated orientation when none is bound to the active runtime.

The backend clinical methods already fail closed on missing orientation, image mismatch, missing FOP/Xi, calibration and manual landmark conditions; its established regression suite checks absent/wrong image and rotation/mirror invariance with **synthetic geometry**. W1 CI now calls that suite and checks that this scientific contract continues matching the source implementation.

## The difference between scientific definition and clinical authorization

The W1 JSON contract `docs/audits/schemas/cephalo_r23g8_w1_atlas33_orientation_dependencies_v1.json` is explicitly `SOURCE_ORIENTATION_OBLIGATIONS_PREVIEW_ONLY__NOT_RUNTIME_MEASUREMENT_AUTHORITY`. Its UI resolver `cephaloR23G8W1OrientationRequirements.ts` is **Atlas-profile scoped** and lists direct landmarks, constructions, manual identity, same-image orientation and calibration **only when the clinician selects one of these four rows**. UI always states "orientation non vérifiée dans cet aperçu"; there is **no new Focus, value, norm, diagnosis, report or patient write**. Existing `resolveR23G3RuntimeFocus` still requires actual exact typed `focus_evidence`, checked at runtime, and the selected row becoming available is not evidence by itself.

This must **never** be described as unlocking four patient measurements. Published source obligation ≠ verified same-image anatomical source ≠ clinician-approved diagnosis.

## Audit and test gates

`python -m scripts.cephalo_r23g8_w1_orientation_coverage --output <path>` compares: exact 33 Atlas identities, prior G7 8/3/22 registry, exact W1 source order 4/14/18/24 and original gates, backend canonical method IDs and direct landmark tuples, canonical construction constants, original manual requirements and same-source/ref gating. It fails on drift, identity aliases and unauthorized clinical promotion. New summary should equal:

| Published frontend source obligations | Count |
|---|---:|
| LOT06 registry | 8 |
| G7 display-only Atlas obligations | 3 |
| W1 same-image orientation obligations | 4 |
| Still unpublished frontend Focus dependencies | 18 |

Backend contract tests run *real* `ImageOrientationEvidence` schema and source/mirror cases; this is **technical evidence**, not a clinical gold standard. A human must independently verify image orientation on a representative, consented test dataset, manual PNS/commissure/FOP/Xi placement, source-image binding/edits, sign conventions and inter-/intra-observer repeatability before any clinical GO. Synthesis of residuals: 18 outstanding conditional obligations in groups W2 dental/occlusal and W3 craniomandibular, not absent methods by default.

## GO / NO-GO

**W1 can be technically closed** only on exact SHA with positive Python+frontend+backend orientation CI and source-ledger artifact, desktop-only visual BEFORE/AFTER and two documented adversarial perspectives. **Clinical status remains NO-GO** until independent clinical evidence, validated orientation provenance in the active study and signed review. PR #911 stays DRAFT; do not merge or deploy as part of W1.
