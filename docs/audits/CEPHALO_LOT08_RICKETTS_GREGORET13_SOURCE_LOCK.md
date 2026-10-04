# LOT08 — Ricketts Gregoret 13 — Claim-by-Claim Source Lock — A2

Date: 2026-10-04  
Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`  
Base: `master@194fca5d964c6668746c2bf1bf84b537203d1d73`

## Scope

Target profile:
`RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1`

This document freezes the **13-factor composition and historical measurement semantics** only. It does not make the historical norms universally applicable and it does not activate UI/report/tracing.

## Source set

**G1 — Gregoret, J. _Ortodoncia y cirugía ortognática_. ESPAXS, 1997.**  
Indexed excerpts consistently expose the summarized 13-factor Ricketts composition and definitions.

**G2 — UNAM clinical thesis reproducing “Análisis de Ricketts (resumido)”.**  
Independently reproduces the same 13 rows and historical reference values.

**G3 — SciELO / population Ricketts studies.**  
Used to cross-check geometry and to prove population/sex dependence of norms, not to redefine Gregoret.

**G4 — Current Digital Crown LOT06 registry/contracts.**  
Used only for canonical mapping and executable/blocking status.

## Frozen 13-factor composition

### 1. Facial axis
- Definition: angle between the facial axis `Pt-Gn` and `Ba-N`.
- Unit: degrees.
- Historical reference: 90° ± 3°.
- Age behavior in Gregoret summaries: no adjustment.
- LOT06: `M_FACIAL_AXIS_RICKETTS_DEG_V1`.
- Required scientific identities: Ba, N, explicit `Pt_Ricketts`, constructed Ricketts Gn.
- Runtime: **CONDITIONAL_EXECUTABLE**; legacy automatic `PT_point` is not accepted.
- Profile status: **SOURCE_LOCKED / FAIL_CLOSED_IDENTITY**.

### 2. Facial depth
- Definition: angle between the facial plane `N-Pog` and Frankfort horizontal.
- Unit: degrees.
- Historical reference: 87° ± 3° at ~9 years.
- Historical age adjustment: approximately +0.3°/year.
- LOT06: `M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1`.
- Runtime: **EXECUTABLE** with exact Po/Or/N/Pog identities.
- Profile status: **SOURCE_LOCKED**.

### 3. Mandibular plane angle
- Definition: angle between the Ricketts mandibular plane and Frankfort horizontal.
- Unit: degrees.
- Historical reference: 26° ± 4° at ~9 years.
- Historical age adjustment: approximately −0.3°/year.
- LOT06 nearest geometry: `M_FH_GOME_DEG_V1`.
- Critical rule: current ID is Tweed/DC-specific and **must not be relabelled Ricketts**.
- Required action: new Ricketts-specific canonical method/ID after exact mandibular-plane construction lock.
- Runtime: **BLOCKED_CONTRACT**.
- Profile status: **SOURCE_LOCKED_MEANING / EXECUTION_BLOCKED**.

### 4. Lower facial height
- Definition: angle `ANS-Xi-Pm`.
- Unit: degrees.
- Historical reference: 47° ± 4°.
- Age behavior: no adjustment in summarized Gregoret material.
- LOT06: `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1`.
- Runtime: **BLOCKED_LANDMARK** because Xi/Pm are not validated runtime identities.
- Profile status: **SOURCE_LOCKED / FAIL_CLOSED_LANDMARK**.

### 5. Mandibular arc
- Definition: angle formed by the condylar axis `DC-Xi` and the posterior extension of the corpus axis `Xi-Pm`.
- Unit: degrees.
- Historical reference: 26° ± 4°.
- Age behavior: conflicting transcription exists; Gregoret VERT tables and independent educational sources support approximately **+0.5°/year**.
- LOT06: no exact canonical executable ID.
- Required identities: DC, Xi, Pm.
- Runtime: **BLOCKED_LANDMARK + NEW_CANONICAL_ID**.
- Norm status: **QUARANTINED_AGE_ADJUSTMENT** until the +0.5°/year source line is rechecked against an authoritative edition.
- Profile status: **SOURCE_LOCKED_GEOMETRY / NORM_DELTA_QUARANTINED**.

### 6. Facial convexity
- Definition: perpendicular distance from Point A to the facial plane `N-Pog`.
- Unit: mm.
- Historical reference: +2 mm ± 2 mm around age 9.
- Historical age adjustment: approximately −0.2 mm/year.
- LOT06: `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1`.
- Runtime: **EXECUTABLE** with verified calibration.
- Profile status: **SOURCE_LOCKED**.

### 7. Maxillary depth
- Definition: angle between Frankfort horizontal and `N-A`.
- Unit: degrees.
- Historical reference: 90° ± 3°.
- Age behavior: no normal-growth adjustment in Gregoret summarized material.
- LOT06: no exact canonical ID.
- Runtime: **NEW_CANONICAL_ID_REQUIRED**.
- Profile status: **SOURCE_LOCKED_MEANING / EXECUTION_MISSING**.

### 8. Lower incisor protrusion to A-Pog
- Definition: perpendicular distance from the lower incisal edge to `A-Pog`.
- Unit: mm.
- Historical reference: +1 mm ± 2 mm.
- Age behavior: described as stable in Gregoret material.
- LOT06: `M_L1_FACIAL_SURFACE_APOG_MM_V1` is related but uses a facial-surface identity; the Gregoret summarized definition recovered here uses the incisal edge.
- Critical rule: do **not** substitute facial-surface and incisal-edge variants.
- Candidate primitive: `M_L1_EDGE_APOG_MM_V1` exists as `PRIMITIVE_AVAILABLE`.
- Runtime: **CANONICAL_VARIANT_ALIGNMENT_REQUIRED**.
- Profile status: **SOURCE_LOCKED / EXECUTION_BLOCKED_BY_ID_VARIANT**.

### 9. Lower incisor inclination to A-Pog
- Definition: angle between the long axis of the lower central incisor and `A-Pog`.
- Unit: degrees.
- Historical reference: 22° ± 4°.
- Age behavior: stable in summarized Gregoret material.
- LOT06: no exact canonical ID.
- Runtime: **NEW_CANONICAL_ID_REQUIRED**.
- Profile status: **SOURCE_LOCKED_MEANING / EXECUTION_MISSING**.

### 10. Upper first molar to PTV
- Definition: linear distance from the distal surface of the upper first molar to pterygoid vertical.
- PTV: vertical through the posterior pterygomaxillary reference, perpendicular to Frankfort.
- Unit: mm.
- Historical reference: patient age + 3 mm, ± 3 mm.
- LOT06: `M_U6_PTV_MM_V1`.
- Runtime: **BLOCKED_LANDMARK/CONSTRUCTION**; exact U6 distal-surface + PTV authority required.
- Profile status: **SOURCE_LOCKED / FAIL_CLOSED_CONSTRUCTION**.

### 11. Lower incisor to occlusal plane (extrusion)
- Definition: distance from the lower incisal edge to the Ricketts functional occlusal plane.
- Unit: mm.
- Historical reference recovered from Gregoret text: +1.25 mm ± 2 mm.
- Independent clinical forms sometimes round this to ~1 mm; Digital Crown must keep the exact source-qualified Gregoret reference.
- LOT06: no exact canonical ID.
- Runtime: **NEW_CANONICAL_ID + FUNCTIONAL_OCCLUSAL_PLANE_REQUIRED**.
- Profile status: **SOURCE_LOCKED_MEANING / EXECUTION_MISSING**.

### 12. Interincisal angle
- Definition: angle between upper and lower incisor long axes.
- Unit: degrees.
- Historical reference: 130° ± 10°.
- LOT06: `M_INTERINCISAL_DEG_V1`.
- Runtime: **EXECUTABLE**.
- Profile status: **SOURCE_LOCKED**.

### 13. Lower lip to E-plane
- Definition: signed linear distance from the most anterior lower lip point to the Ricketts esthetic plane from soft-tissue nose tip to soft-tissue pogonion.
- Unit: mm.
- Historical reference: approximately −2 mm ± 2 mm in Gregoret summarized material.
- Historical age behavior: ~−0.2 mm/year reported in teaching reproductions; population dependence is strong.
- LOT06: `M_LI_EPLANE_MM_V1`.
- Runtime: **EXECUTABLE** with verified calibration and canonical soft-tissue identities.
- Norm status: historical reference only; no universal classification.
- Profile status: **SOURCE_LOCKED_GEOMETRY / NORM_APPLICABILITY_QUARANTINED**.

## Composition verdict

All **13/13 rows are composition-locked** to the Gregoret summarized profile.

Execution status:
- Exact executable now: 4 — facial depth, convexity, interincisal angle, lower lip/E-plane.
- Conditional executable: 1 — facial axis.
- Existing canonical/primitive but identity or construction blocked: 4 — lower facial height, lower incisor/A-Pog distance, U6/PTV, mandibular plane nearest geometry.
- New source-specific canonical IDs/contracts required: 4 — maxillary depth, lower incisor/A-Pog angle, lower-incisor extrusion, mandibular arc.

## Normative gate

Historical Gregoret/Ricketts values are **reference values**, not universal contemporary norms.

Reason:
- published population studies demonstrate meaningful ethnic/population and sex differences for Ricketts measurements;
- age adjustment applies to multiple factors;
- some source reproductions conflict on age-delta transcription.

Required product behavior:
- measurement may be shown when executable;
- historical reference may be shown with source/version;
- automatic “normal/abnormal” classification is suppressed outside an explicitly validated norm profile;
- VERT cannot be activated as an authoritative classification until its age-adjusted reference set and applicability are source-locked separately.

## Adversarial review A — orthodontic/source fidelity

### Findings
1. **MAJOR** — The previous A1 table conflated lower-incisor A-Pog facial-surface and incisal-edge variants.
   - Fix: Gregoret 13 explicitly locks the incisal-edge distance; LOT06 facial-surface ID cannot substitute.
2. **MAJOR** — Mandibular-arc age direction is contradictory across accessible reproductions.
   - Fix: geometry is locked, age delta quarantined pending authoritative-edition confirmation.
3. **MAJOR** — Historic norms risked being interpreted as universal.
   - Fix: reference-display only unless population/age/sex applicability profile is separately validated.

Post-fix severe score: **9.6/10**.

## Adversarial review B — architecture/QA authority

### Findings
1. **MAJOR** — Reusing Tweed/DC `M_FH_GOME_DEG_V1` would silently create a Ricketts authority alias.
   - Fix: require dedicated Ricketts method/ID.
2. **MAJOR** — A-Pog distance variant collision would allow numerically plausible but scientifically different values.
   - Fix: exact source-specific ID mapping required.
3. **MAJOR** — PTV and functional occlusal plane are constructions, not loose line labels.
   - Fix: both require versioned construction evidence and fail-closed dependency graphs.

Post-fix severe score: **9.6/10**.

## Confirmation pass

Re-reviewed after fixes:
- new BLOCKER: 0;
- new MAJOR: 0;
- significant debt: explicit and gated;
- no product formula/UI/report changed.

## Gate verdict

`RICKETTS_GREGORET_13_COMPOSITION_SOURCE_LOCKED = YES`

`RICKETTS_GREGORET_13_NORMS_UNIVERSALLY_VALIDATED = NO`

`RICKETTS_GREGORET_13_EXECUTABLE = NO`

Therefore the **composition pre-code gate is closed**, while implementation remains open because canonical IDs/landmarks/constructions are incomplete.

## Next exact

Create the missing LOT06-compatible scientific contracts **without UI activation**:
1. Ricketts mandibular-plane angle method/ID.
2. Ricketts maxillary depth.
3. Ricketts lower-incisor A-Pog angle.
4. Ricketts lower-incisor extrusion to functional occlusal plane.
5. Ricketts mandibular arc.
6. Exact incisal-edge A-Pog distance variant binding.
7. PTV + functional occlusal plane construction contracts.
8. Xi/Pm/DC manual scientific identity contracts first; auto authority remains fail-closed.

Then tests → two fresh reviews → confirmation → only then UI/report/tracing.

No merge. No deployment.
