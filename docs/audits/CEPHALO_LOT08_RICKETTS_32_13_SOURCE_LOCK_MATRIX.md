# LOT08 — Ricketts Complete / Summarized Source-Lock Matrix — A1

Date: 2026-10-04  
Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`  
Base: `master@194fca5d964c6668746c2bf1bf84b537203d1d73`

## Goal

Resolve the naming/composition conflict behind "Ricketts 32" and "Ricketts 13" before implementation, then map the source-supported profiles to the current LOT06 canonical registry.

## Verified source hierarchy for this A1

### S1 — Facad official release notes, v3.12
Facad officially lists:
- `Ricketts (32 F)`, attributed to Fernández Sánchez & Da Silva Filho, *Atlas Cefalometría y Análisis Facial* (2009).
- `Ricketts (13 F)`, also attributed to the same Atlas (2009).

Official source:
https://www.facad.com/wp/wp-content/uploads/2020/12/FacadReleaseNotes_3.12.pdf

This proves **vendor profile names**, not the exact public measurement membership.

### S2 — Fernández Sánchez & Da Silva Filho, Atlas Cefalometría y Análisis Facial (2009)
Publicly indexed chapter text from the Atlas states:
- the developed Ricketts analysis reached **33 factors** in six fields;
- chapter 13.4 presents a **12-factor summary**.

The chapter therefore does **not** transparently match Facad's public labels 32 F / 13 F.

### S3 — Published 32-factor implementation
A Korean cephalometric publication contains an explicit 32-factor Ricketts table grouped into six fields. This provides a concrete complete 32-row implementation but is not, by itself, proof that Facad's exact 32 F composition is identical.

### S4 — Gregoret summarized 13-factor profile
Multiple academic sources attribute a **13-factor summarized Ricketts** to Gregoret (1997), *Ortodoncia y cirugía ortognática: diagnóstico y planificación*. The recovered 13-factor membership is internally consistent across sources.

## Critical discrepancy

There are at least four distinct public compositions:
1. Facad vendor label: 32 F.
2. Facad vendor label: 13 F.
3. Atlas 2009 chapter: 33-factor complete + 12-factor summary.
4. Gregoret 1997 lineage: 13-factor summarized profile.

Therefore Digital Crown must **not** call a source-locked profile simply "the Ricketts 32" or "the Ricketts 13" without an edition/source qualifier.

---

## Profile decision

### Main complete profile
Provisional ID:
`RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`

Source authority:
Fernández Sánchez & Da Silva Filho, 2009 Atlas chapter.

Reason:
this is the source Facad itself cites, and the indexed chapter explicitly describes 33 factors.

Status:
COMPOSITION SOURCE-LOCKED to the Atlas 2009 33-factor table; execution remains partial/fail-closed. Canonical profile: `docs/audits/schemas/ortho_lot08_ricketts_atlas2009_complete33_protocol_profile_v1.json`.

### Main summarized profile
Provisional ID:
`RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1`

Source authority:
Gregoret 1997 lineage as reproduced consistently in academic material.

Status:
COMPOSITION IDENTIFIED.

### Compatibility targets
- `FACAD_RICKETTS_32F_COMPATIBILITY_TARGET`
- `FACAD_RICKETTS_13F_COMPATIBILITY_TARGET`

These are product-parity targets only until the exact Facad membership/export is independently observed. They must never become scientific source IDs.

---

# A. Published 32-factor compatibility implementation matrix

Source membership observed in a published 32-factor Ricketts implementation. This section is retained for compatibility comparison and is **not** the authoritative Atlas 2009 33-factor profile.

| # | Factor | LOT06 / registry mapping | Current state |
|---:|---|---|---|
| 1 | Molar relation | `M_RICKETTS_MOLAR_RELATION_FOP_MM_V1` | CONDITIONAL_EXECUTABLE: manual `L6_DISTAL_Ricketts` + `U6_DISTAL_Ricketts` + source-locked FOP + verified calibration |
| 2 | Canine relation | `M_RICKETTS_CANINE_RELATION_FOP_MM_V1` | CONDITIONAL_EXECUTABLE: manual `L3_CUSP_Ricketts` + `U3_CUSP_Ricketts` + source-locked FOP + verified calibration |
| 3 | Incisor overjet | `M_RICKETTS_OVERJET_FOP_MM_V1` | CONDITIONAL_EXECUTABLE: `L1_incisal` + `U1_incisal` + source-locked FOP + verified calibration; positive upper-anterior |
| 4 | Incisor overbite | `M_RICKETTS_OVERBITE_FOP_MM_V1` | SOURCE_LOCKED_BLOCKED: source sign known (open bite negative); superior/inferior image axis not evidenced; no runtime promotion |
| 5 | Lower incisor extrusion | `M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1` | CONDITIONAL_EXECUTABLE: source-locked FOP + `L1_incisal/L1_apex` crownward-positive sign + verified calibration |
| 6 | Interincisal angle | `M_INTERINCISAL_DEG_V1` | EXECUTABLE |
| 7 | Convexity | `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1` | EXECUTABLE with verified calibration |
| 8 | Lower face height | `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1` | CONDITIONAL_EXECUTABLE: source-locked Xi from manual/manual-corrected R1-R4 + anatomical Frankfort, manual/manual-corrected `Pm_Ricketts` + ANS |
| 9 | Upper molar position | `M_U6_PTV_MM_V1` | CONDITIONAL_EXECUTABLE: manual/manual-corrected `U6_DISTAL_Ricketts` + manual/manual-corrected `PR_Ricketts_PTV` + anatomical Frankfort + verified calibration |
| 10 | Mandibular incisor protrusion | `M_L1_EDGE_APOG_MM_V1` | EXECUTABLE: perpendicular incisal-edge/tip distance to A-Pog; anterior positive; previous facial-surface mapping rejected |
| 11 | Maxillary incisor protrusion | `M_RICKETTS_U1_APOG_PROTRUSION_MM_V1` | EXECUTABLE: perpendicular U1 incisal-edge distance to A-Pog; anterior positive |
| 12 | Mandibular incisor inclination to A-Pog | `M_RICKETTS_L1_APOG_INCLINATION_DEG_V1` | EXECUTABLE |
| 13 | Maxillary incisor inclination to A-Pog | `M_RICKETTS_U1_APOG_INCLINATION_DEG_V1` | EXECUTABLE: explicit `U1_incisal/U1_apex` axis vs A-Pog |
| 14 | Occlusal plane to ramus/Xi | `M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1` | SOURCE_LOCKED_BLOCKED: source sign known (+ plane above Xi / − below); superior/inferior image axis not evidenced |
| 15 | Occlusal plane inclination | `M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1` | CONDITIONAL_EXECUTABLE: source-locked FOP + canonical Xi + manual Pm |
| 16 | Lip protrusion | `M_LI_EPLANE_MM_V1` | EXECUTABLE with calibration/canonical soft identities |
| 17 | Upper lip length | `M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1` | CONDITIONAL_EXECUTABLE: ANS + manual `LABIAL_COMMISSURE_Ricketts` + calibration |
| 18 | Lip embrasure/comissure to occlusal plane | `M_RICKETTS_COMMISSURE_FOP_MM_V1` | SOURCE_LOCKED_BLOCKED: source sign known (negative when FOP below commissure); superior/inferior image axis not evidenced |
| 19 | Facial depth | `M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1` | EXECUTABLE |
| 20 | Facial axis | `M_FACIAL_AXIS_RICKETTS_DEG_V1` | EXECUTABLE only with explicit/audited `Pt_Ricketts`; auto legacy Pt fails closed |
| 21 | Facial taper / facial cone | `M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1` | CONDITIONAL_EXECUTABLE: N-Pog + source-locked Ricketts mandibular plane |
| 22 | Maxillary depth | `M_RICKETTS_MAXILLARY_DEPTH_NA_FH_DEG_V1` | EXECUTABLE |
| 23 | Maxillary height | `M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1` | CONDITIONAL_EXECUTABLE: N-CF-A, CF = anatomical FH ∩ source-locked PTV |
| 24 | Palatal plane | `M_RICKETTS_PALATAL_PLANE_FH_DEG_V1` | SOURCE_LOCKED_BLOCKED: directional sign now source-known; superior/inferior image axis not evidenced, so no signed runtime |
| 25 | Mandibular plane angle | `M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1` | CONDITIONAL_EXECUTABLE: explicit `MP_ANGLE_INFERIOR_Ricketts` + Me + anatomical Frankfort; generic Go/Go-Gn substitution forbidden |
| 26 | Cranial deflection | `M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1` | EXECUTABLE: anatomical FH vs Ba-N |
| 27 | Anterior cranial length | `M_RICKETTS_ANTERIOR_CRANIAL_LENGTH_CC_N_MM_V1` | CONDITIONAL_EXECUTABLE: Atlas2009 CC + N + calibration |
| 28 | Posterior facial height | `M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1` | CONDITIONAL_EXECUTABLE: manual `GO_Ricketts_PFH` + canonical CF + calibration |
| 29 | Ramus position | `M_RICKETTS_RAMUS_POSITION_FH_CFXI_DEG_V1` | CONDITIONAL_EXECUTABLE: anatomical FH + canonical CF + canonical Xi |
| 30 | Porion location / TMJ | `M_RICKETTS_PORION_LOCATION_PTV_MM_V1` | CONDITIONAL_EXECUTABLE: source-locked PTV + anatomical Po + calibration; posterior negative |
| 31 | Mandibular arc | `M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1` | CONDITIONAL_EXECUTABLE: manual/manual-corrected `DC_Ricketts` + source-locked Xi + manual/manual-corrected `Pm_Ricketts` |
| 32 | Corpus length | `M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1` | CONDITIONAL_EXECUTABLE: canonical Xi + manual Pm + calibration |

### 32-factor runtime summary
- Exact executable canonical members: **10** (#6, #7, #10, #11, #12, #13, #16, #19, #22, #26).
- Conditional executable: **18** (#1, #2, #3, #5, #8, #9, #15, #17, #20, #21, #23, #25, #27, #28, #29, #30, #31, #32).
- Primitive/geometry exists but cannot yet be labelled Ricketts: **0**.
- Source-locked but blocked: **4** (#4 overbite; #14 FOP→Xi; #18 commissure→FOP; #24 palatal-plane angle). Their source signs are known; the remaining gate is explicit superior/inferior image orientation evidence.
- New source-specific canonical contract required: **0**.
- Total accounted factors: **32/32**.

This proves that the current five-measure LOT06 Ricketts pack is only a seed, not a complete protocol.

---

# B. Gregoret-lineage summarized 13-factor matrix

Recovered membership:
1. lower incisor to occlusal plane / lower incisor extrusion;
2. interincisal angle;
3. facial convexity;
4. lower facial height;
5. lower incisor to A-Pog;
6. lower incisor inclination to A-Pog;
7. upper molar to PTV;
8. lower lip to E-plane;
9. facial axis;
10. facial depth;
11. mandibular plane angle;
12. maxillary depth;
13. mandibular arc.

| # | Factor | LOT06 / registry mapping | Current state |
|---:|---|---|---|
| 1 | Lower incisor extrusion to occlusal plane | `M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1` | CONDITIONAL_EXECUTABLE: explicit `FOP_PREMOLAR_Ricketts` + `FOP_MOLAR_Ricketts` + `L1_incisal/L1_apex` + verified calibration; crownward positive |
| 2 | Interincisal angle | `M_INTERINCISAL_DEG_V1` | EXECUTABLE |
| 3 | Facial convexity | `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1` | EXECUTABLE with verified calibration |
| 4 | Lower facial height | `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1` | CONDITIONAL_EXECUTABLE: source-locked Xi construction from manual/manual-corrected R1-R4 + anatomical Frankfort; manual/manual-corrected `Pm_Ricketts` + ANS required |
| 5 | Lower incisor to A-Pog | `M_L1_EDGE_APOG_MM_V1` | EXECUTABLE: explicit incisal-edge variant |
| 6 | Lower incisor inclination to A-Pog | `M_RICKETTS_L1_APOG_INCLINATION_DEG_V1` | EXECUTABLE |
| 7 | Upper molar to PTV | `M_U6_PTV_MM_V1` | CONDITIONAL_EXECUTABLE: manual/manual-corrected `U6_DISTAL_Ricketts` + source-locked PTV from manual `PR_Ricketts_PTV` + anatomical Frankfort + verified calibration |
| 8 | Lower lip to E-plane | `M_LI_EPLANE_MM_V1` | EXECUTABLE with calibration/canonical soft identities |
| 9 | Facial axis | `M_FACIAL_AXIS_RICKETTS_DEG_V1` | CONDITIONAL: explicit/audited Pt_Ricketts |
| 10 | Facial depth | `M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1` | EXECUTABLE |
| 11 | Mandibular plane angle | `M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1` | CONDITIONAL_EXECUTABLE: explicit `MP_ANGLE_INFERIOR_Ricketts` + Me + anatomical Frankfort; generic Go/Go-Gn substitution forbidden |
| 12 | Maxillary depth | `M_RICKETTS_MAXILLARY_DEPTH_NA_FH_DEG_V1` | EXECUTABLE |
| 13 | Mandibular arc | `M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1` | CONDITIONAL_EXECUTABLE: manual/manual-corrected `DC_Ricketts` + source-locked Xi + manual/manual-corrected `Pm_Ricketts` |

### 13-factor runtime summary
- Exact executable: **7** (#2, #3, #5, #6, #8, #10, #12).
- Conditional executable: **6** (#1 lower-incisor extrusion; #4 lower facial height; #7 upper molar/PTV; #9 facial axis; #11 mandibular plane; #13 mandibular arc).
- Source-locked but blocked by landmark authority: **0**.
- No historical norm or VERT classification is activated by these execution states.

---

# C. Atlas 2009 composition discrepancy

The indexed Atlas chapter states:
- complete analysis = **33 factors**;
- simplified summary = **12 factors**.

The 12-factor summary contains:
- Facial axis.
- Facial depth.
- Posterior facial height.
- Mandibular plane angle.
- Lower facial height.
- Mandibular arc.
- Facial convexity.
- Maxillary depth.
- Lower incisor protrusion.
- Lower incisor inclination.
- Upper molar position.
- Lip protrusion.

This is **not identical** to the recovered Gregoret 13-factor profile, which adds lower-incisor extrusion and interincisal angle but does not include posterior facial height.

Therefore:
- `RICKETTS_ATLAS_2009_SUMMARY_12_PROTOCOL_V1` and
- `RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1`

must remain separate scientific profiles if both are retained.

---

# D. Product decision after source-lock pass

Recommended Digital Crown UI family:

**Ricketts**
- **Complet — Atlas 2009 (33 facteurs)** — authoritative complete target.
- **Résumé clinique — Gregoret 1997 (13 facteurs)** — practical reduced target.
- **Résumé Atlas 2009 (12 facteurs)** — optional only if product value justifies a third lateral variant.
- **Historique 1960** — optional reference profile, not default.
- **Frontal / PA** — separate future modality/profile.

Do **not** expose "32 facteurs" as the canonical scientific profile unless the exact 32-factor source/version chosen by Digital Crown is explicitly named. Keep Facad's 32 F as a compatibility benchmark.

---

# E. Adversarial review A — orthodontic/source fidelity

### Finding 1 — MAJOR
The earlier plan `RICKETTS_COMPREHENSIVE_32_PROTOCOL_V1` treated the vendor label 32 F as if it were the authoritative scientific composition. Public evidence shows the Atlas Facad cites actually describes 33 factors.

**Fix:** main complete profile becomes source-qualified `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`; Facad 32 F remains a compatibility target.

### Finding 2 — MAJOR
The earlier plan treated "13 factor" as one unique profile. Public sources show Atlas 2009 has a 12-factor summary, while Gregoret-lineage material has a distinct 13-factor summary.

**Fix:** split Atlas-12 and Gregoret-13.

### Post-fix severe score
**9.6/10**

Residual debt:
Facad's exact proprietary/public 32F/13F row membership has not been independently exported/observed, so parity cannot yet be claimed.

---

# F. Adversarial review B — architecture/runtime authority

### Finding 1 — MAJOR
Current LOT06 `RICKETTS_V1` contains only facial depth, convexity, E-line Ls/Li and facial axis. Treating it as "Ricketts complete" would hide roughly two dozen missing source-specific contracts.

**Fix:** LOT06 pack remains provisional infrastructure; LOT08 profiles receive their own exact membership and must map every row to a canonical ID.

### Finding 2 — MAJOR
Reusing `M_FH_GOME_DEG_V1` as Ricketts mandibular-plane angle would silently import Tweed/DC semantics.

**Fix:** require a Ricketts-specific canonical method/ID even if the numerical geometry later proves equivalent.

### Post-fix severe score
**9.5/10**

---

# G. Confirmation pass

Re-reviewed the source/profile architecture after the fixes.

- New BLOCKER: 0.
- New MAJOR: 0.
- Significant open scientific work: explicit and accepted as open, not hidden.

A1 matrix framing is converged. **Gregoret-lineage 13-factor execution contracts remain source-locked with 7 executable + 6 conditional rows and 0 blocked landmark rows. Atlas/33 is mapped 33/33 with 10 executable + 19 conditional + 4 orientation-blocked rows; direct Facad parity remains open.**

## Gate

`RICKETTS_GREGORET13_SOURCE_LOCK = CONTRACT_COMPLETE / VALIDATION_PENDING`  
`RICKETTS_ATLAS2009_COMPLETE33_COMPOSITION_LOCK = COMPLETE`  
`RICKETTS_ATLAS2009_COMPLETE33_EXECUTION_LOCK = PARTIAL / OPEN`  
`FACAD_RICKETTS_32F_13F_PARITY = UNOBSERVED / OPEN`

## Next exact

1. Complete validation/convergence of the Gregoret 13 source-lock on the final exact HEAD.
2. Continue the Atlas 2009 complete-profile contracts with the 6 remaining new canonical contracts in structures internes (#26-#33), plus the explicitly quarantined signed/label conflicts.
3. Keep norms, age/sex interpretation, VERT and clinical classification disabled until separately validated.
4. Only then wire any new UI/report/tracing for the expanded protocol.
5. Keep Facad 32F/13F as parity checks, not scientific source identifiers.

No merge. No deployment.
