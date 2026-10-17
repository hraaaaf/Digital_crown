# Digital Crown — CEPH-UXCLIN-01 / R23-G8-W3 — Ricketts Atlas2009 craniomandibular source dependencies

2026-10-17. **DESKTOP-only / SOURCE DESCRIPTION, NOT CLINICAL MEASUREMENT APPROVAL.**

## Purpose and authority

Complete the 11 Atlas2009 Ricketts factor **frontend dependency descriptors** not already documented by LOT06, G7, W1 or W2. All factors already have conditional backend method definitions and must continue to be validated through the existing active source-image typed evidence chain. W3 adds no landmark placement, measurement formula, patient data, diagnosis, normative table or SVG Focus authorization.

Primary project source: `backend/data/cephalometry/ricketts_atlas2009_complete33_protocol_profile_v1.json`; methods `backend/services/cephalo_canonical_analysis_v2.py`; constructors `backend/services/cephalo_canonical_constructions_v2.py`. Clinical source locks: `docs/audits/CEPHALO_LOT08_RICKETTS_32_13_SOURCE_LOCK_MATRIX.md`, `CEPHALO_LOT08_RICKETTS_ATLAS33_WAVE_B_SOURCE_LOCK.md` and `CEPHALO_LOT08_RICKETTS_ATLAS33_WAVE_C_SOURCE_LOCK.md`.

| Factor | Method/source identity | Direct landmarks | Constructed sources / gate |
|---|---|---|---|
| #8 Lower face height | `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1` | `ANS`, manual `Pm_Ricketts` | Xi from R1–R4 + anatomical FH |
| #21 Facial taper | `M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1` | `N`, `Pog_hard` | Ricketts mandibular plane `MP_ANGLE_INFERIOR_Ricketts`→Me, not arbitrary Go-Me |
| #23 Maxillary height | `M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1` | `N`, `A` | CF via PTV and anatomical FH; source manual `PR_Ricketts_PTV` |
| #25 Mandibular plane / FH | `M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1` | `Po_anatomic`, `Or`, `MP_ANGLE_INFERIOR_Ricketts`, `Me` | Source Ricketts MP, **no auto-alias** to generic Go |
| #27 Anterior cranial length | `M_RICKETTS_ANTERIOR_CRANIAL_LENGTH_CC_N_MM_V1` | `N` | CC from Ba–N intersection with `Pt_Ricketts` (manual)–Gn constructed from `N,Pog_hard,Go,Me`; verified mm calibration |
| #28 Posterior facial height | `M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1` | manual `GO_Ricketts_PFH` | CF canonical via PTV, verified mm calibration |
| #29 TOTAL facial height | `M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1` | `Ba,N`, manual `Pm_Ricketts` | Xi and Ba–N angle (deg). Historical Atlas duplicate label **posterior facial height** rejected for this line, never merged with #28 mm |
| #30 Ramus position | `M_RICKETTS_RAMUS_POSITION_FH_CFXI_DEG_V1` | `Po_anatomic,Or` | both canonical CF and Xi; angle |
| #31 Porion position | `M_RICKETTS_PORION_LOCATION_PTV_MM_V1` | `Po_anatomic` | PTV from manual PR and FH; signed anterior axis; verified mm calibration |
| #32 Mandibular arc | `M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1` | manual `DC_Ricketts,Pm_Ricketts` | Xi canonical; angle |
| #33 Corpus length | `M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1` | manual `Pm_Ricketts` | Xi canonical, verified mm calibration |

### Original recursive construction lineage (not hand-built geometry)

- `RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1` = `R1_Ricketts,R2_Ricketts,R3_Ricketts,R4_Ricketts,Po_anatomic,Or`; R1–R4 are manual/manual-corrected.
- `RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1` = manual `PR_Ricketts_PTV`, `Po_anatomic,Or`.
- `RICKETTS_CF_FH_PTV_INTERSECTION_V1` = anatomical Frankfort intersecting constructed PTV. **CF→PTV**, not independent generic CF.
- `RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1` = `N,Pog_hard,Go,Me`, constructed by canonical line intersection.
- `RICKETTS_CC_ATLAS2009_BAN_PTGN_INTERSECTION_V1` = `Ba,N,Pt_Ricketts` (Pt manual) and constructed **Gn**. Full transitive IDs are `Ba,N,Pt_Ricketts,Pog_hard,Go,Me`. **CC→Gn; NOT CC→PTV and NOT Pt_Ricketts=PR_Ricketts_PTV**.
- `RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1` = `MP_ANGLE_INFERIOR_Ricketts,Me` (explicit source point; do not invent a manual origin gate if the current backend does not require it).

**Indirect manually controlled landmarks in constructed dependencies:** Xi requires R1–R4 manual/manual-corrected; PTV and therefore CF require manual `PR_Ricketts_PTV`; CC requires manual `Pt_Ricketts` (which is NOT `PR_Ricketts_PTV`). The direct landmark requirements remain separate. A source name cannot be silently interpreted as an automatically validated patient position.

Every construction requires its original source-image and availability authority. Every unit mm requires verified source calibration. "Present landmark IDs" in a frontend display are **not** active graph provenance, manual validation or scientific truth.

### Actual changed components

Contract: `docs/audits/schemas/cephalo_r23g8_w3_atlas33_craniomandibular_dependencies_v1.json` lists eleven exact Atlas row/method/gate IDs, direct and transitive construction point IDs, validated manual obligations, and calibration/same-image requirements.

Atlas-only reader: `frontend/src/features/ortho/cephaloR23G8W3CranioRequirements.ts`, with a read-only source block in `CephaloR23G2ProtocolPanel.tsx`; Gregoret/McNamara never inherit this preview. Typed runtime `resolveR23G3RuntimeFocus` remains unchanged and fail-closed, even when a preview's direct point IDs are present or a numeric value is stored in an unauthorized row.

Reproducible audit: `python -m scripts.cephalo_r23g8_w3_cranio_coverage --output audit/atlas33-w3.json`. Checks exact original Atlas 33, 11 conditional source rows and gates, literal backend tuples/method IDs, exact original constructors + transitive source chains (CF/PTV vs CC/Gn), strict lack of source aliases, and original calibration/manual method guard. Negative source changes must fail.

## Acceptance / risks

Expected source **descriptor coverage**: LOT06 8 + G7 3 + W1 4 + W2 7 + W3 11 = 33/33 descriptions, no extra Atlas row; **zero** clinically approved patient values or active Focus from this project increment. The JSON ledger must set `clinical_release=false`, `patient_source_goldset_verified=false`, `independent_clinical_review=false`.

Clinical validation remains a separate major gate: qualified, independent expert review of annotated source images, same-image calibration and provenance, actual Gn, CC, CF, Xi, PTV, mandibular plane and tooth landmarks, sign/angle/mirror conventions, inter-/intraobserver reliability, alternative source editions and historical factor 29 conflict. G4 screenshots and synthetic geometry alone are not clinical evidence.

**PR #911 DRAFT; no merge, Vercel deployment, smartphone cephalometry or patient/machine activation.**
