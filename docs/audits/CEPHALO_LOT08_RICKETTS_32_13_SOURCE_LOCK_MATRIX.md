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
COMPOSITION IDENTIFIED; exact row-by-row source lock below is materially recoverable, but several definitions/runtime identities remain blocked.

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

# A. Explicit 32-factor implementation matrix

Source membership observed in the published 32-factor table.

| # | Factor | LOT06 / registry mapping | Current state |
|---:|---|---|---|
| 1 | Molar relation | none | NEW_CANONICAL_ID + molar identities + exact functional occlusal plane |
| 2 | Canine relation | none | NEW_CANONICAL_ID + canine identities |
| 3 | Incisor overjet | `M_OVERJET_MM_V1` | LEGACY_TO_AUDIT; source-specific Ricketts convention not executable |
| 4 | Incisor overbite | `M_OVERBITE_V1` | LEGACY_TO_AUDIT |
| 5 | Lower incisor extrusion | none | NEW_CANONICAL_ID + Ricketts functional occlusal plane |
| 6 | Interincisal angle | `M_INTERINCISAL_DEG_V1` | EXECUTABLE |
| 7 | Convexity | `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1` | EXECUTABLE with verified calibration |
| 8 | Lower face height | `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1` | BLOCKED_LANDMARK: Xi/Pm |
| 9 | Upper molar position | `M_U6_PTV_MM_V1` | BLOCKED_LANDMARK / PTV source contract |
| 10 | Mandibular incisor protrusion | `M_L1_FACIAL_SURFACE_APOG_MM_V1` | BLOCKED_LANDMARK |
| 11 | Maxillary incisor protrusion | none | NEW_CANONICAL_ID |
| 12 | Mandibular incisor inclination to A-Pog | none exact | NEW_CANONICAL_ID |
| 13 | Maxillary incisor inclination to A-Pog | none exact | NEW_CANONICAL_ID |
| 14 | Occlusal plane to ramus/Xi | none | NEW_CANONICAL_ID + Xi + functional occlusal plane |
| 15 | Occlusal plane inclination | none | NEW_CANONICAL_ID + Xi/Pm + functional occlusal plane |
| 16 | Lip protrusion | `M_LI_EPLANE_MM_V1` | EXECUTABLE with calibration/canonical soft identities |
| 17 | Upper lip length | none | NEW_CANONICAL_ID |
| 18 | Lip embrasure/comissure to occlusal plane | none | NEW_CANONICAL_ID + commissure identity |
| 19 | Facial depth | `M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1` | EXECUTABLE |
| 20 | Facial axis | `M_FACIAL_AXIS_RICKETTS_DEG_V1` | EXECUTABLE only with explicit/audited `Pt_Ricketts`; auto legacy Pt fails closed |
| 21 | Facial taper / facial cone | none | NEW_CANONICAL_ID |
| 22 | Maxillary depth | none | NEW_CANONICAL_ID |
| 23 | Maxillary height | none | NEW_CANONICAL_ID + CF |
| 24 | Palatal plane | `M_PALATAL_PLANE_FH_DEG_V1` | PRIMITIVE_AVAILABLE; Ricketts source-specific execution contract still required |
| 25 | Mandibular plane angle | nearest `M_FH_GOME_DEG_V1` | DO NOT RELABEL; current contract is Tweed/DC-specific; Ricketts method ID required |
| 26 | Cranial deflection | none | NEW_CANONICAL_ID |
| 27 | Anterior cranial length | none | NEW_CANONICAL_ID + CC |
| 28 | Posterior facial height | none | NEW_CANONICAL_ID + CF/Go definition |
| 29 | Ramus position | none | NEW_CANONICAL_ID + CF/Xi |
| 30 | Porion location / TMJ | none | NEW_CANONICAL_ID + exact Ricketts construction |
| 31 | Mandibular arc | none | NEW_CANONICAL_ID + DC/Xi/Pm |
| 32 | Corpus length | none | NEW_CANONICAL_ID + Xi/Pm/A-Pog source geometry |

### 32-factor runtime summary
- Immediately executable exact/near-exact canonical members: **4** (#6, #7, #16, #19).
- Conditional executable: **1** (#20 facial axis with explicit Pt_Ricketts).
- Primitive/geometry exists but cannot yet be labelled Ricketts: **2** (#24, #25).
- Existing canonical but blocked/legacy: **5** (#3, #4, #8, #9, #10).
- New source-specific canonical contract required: **20**.

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
| 1 | Lower incisor extrusion to occlusal plane | none | NEW_CANONICAL_ID |
| 2 | Interincisal angle | `M_INTERINCISAL_DEG_V1` | EXECUTABLE |
| 3 | Facial convexity | `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1` | EXECUTABLE |
| 4 | Lower facial height | `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1` | BLOCKED Xi/Pm |
| 5 | Lower incisor to A-Pog | `M_L1_FACIAL_SURFACE_APOG_MM_V1` | BLOCKED_LANDMARK |
| 6 | Lower incisor inclination to A-Pog | none exact | NEW_CANONICAL_ID |
| 7 | Upper molar to PTV | `M_U6_PTV_MM_V1` | BLOCKED_LANDMARK / PTV |
| 8 | Lower lip to E-plane | `M_LI_EPLANE_MM_V1` | EXECUTABLE |
| 9 | Facial axis | `M_FACIAL_AXIS_RICKETTS_DEG_V1` | CONDITIONAL: explicit Pt_Ricketts |
| 10 | Facial depth | `M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1` | EXECUTABLE |
| 11 | Mandibular plane angle | nearest `M_FH_GOME_DEG_V1` | RICKETTS-SPECIFIC METHOD REQUIRED |
| 12 | Maxillary depth | none | NEW_CANONICAL_ID |
| 13 | Mandibular arc | none | NEW_CANONICAL_ID + DC/Xi/Pm |

### 13-factor runtime summary
- Executable now: **4** (#2, #3, #8, #10).
- Conditional executable: **1** (#9).
- Existing-but-blocked: **3** (#4, #5, #7).
- Existing geometry cannot be relabelled: **1** (#11).
- New canonical source-specific contract required: **4** (#1, #6, #12, #13).

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

A1 matrix framing is converged; **Ricketts protocol implementation is not converged**.

## Gate

`RICKETTS_SOURCE_LOCK = PARTIAL / OPEN`

## Next exact

1. Freeze exact 33 Atlas factor definitions/constructions one by one.
2. Freeze exact Gregoret 13 factor definitions/constructions one by one.
3. Create missing canonical LOT06 IDs/contracts, beginning with the 13-factor profile because it reduces the first executable clinical slice.
4. Add explicit manual identities/constructions for Xi, Pm, CF, DC, PTV and Ricketts functional occlusal plane before any auto authority.
5. Only then wire UI/report/tracing.
6. Keep Facad 32F/13F as parity checks, not scientific source identifiers.

No merge. No deployment.
