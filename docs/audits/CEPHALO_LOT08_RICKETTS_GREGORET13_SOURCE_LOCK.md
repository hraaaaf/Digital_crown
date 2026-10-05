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
- Runtime: **BLOCKED_LANDMARK** because `Xi_Ricketts` / `Pm_Ricketts` are not validated runtime identities.
- Profile status: **SOURCE_LOCKED / FAIL_CLOSED_LANDMARK**.

### 5. Mandibular arc
- Definition: angle formed by the condylar axis `DC-Xi` and the posterior extension of the corpus axis `Xi-Pm`.
- Unit: degrees.
- Historical reference: 26° ± 4°.
- Age behavior: conflicting transcription exists; Gregoret VERT tables and independent educational sources support approximately **+0.5°/year**.
- LOT06 canonical ID: `M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1`.
- Required source-specific scientific identities: `DC_Ricketts`, `Xi_Ricketts`, `Pm_Ricketts`.
- Condylar axis: `DC_Ricketts-Xi_Ricketts`.
- Corpus axis: `Xi_Ricketts-Pm_Ricketts`; mandibular arc uses its distal extrapolation at Xi.
- Runtime: **BLOCKED_LANDMARK** — no automatic DC/Xi/Pm authority is validated.
- Norm status: **QUARANTINED_AGE_ADJUSTMENT** until the +0.5°/year source line is rechecked against an authoritative edition.
- Profile status: **SOURCE_LOCKED_GEOMETRY / FAIL_CLOSED_LANDMARK / NORM_DELTA_QUARANTINED**.

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
- LOT06: `M_RICKETTS_MAXILLARY_DEPTH_NA_FH_DEG_V1`.
- Runtime: **EXECUTABLE** through `RICKETTS_MAXILLARY_DEPTH_CANONICAL_DEG_V2`.
- Profile status: **SOURCE_LOCKED / EXECUTABLE**.

### 8. Lower incisor protrusion to A-Pog
- Definition: perpendicular distance from the lower incisal edge to `A-Pog`.
- Unit: mm.
- Historical reference: +1 mm ± 2 mm.
- Age behavior: described as stable in Gregoret material.
- LOT06: `M_L1_FACIAL_SURFACE_APOG_MM_V1` is related but uses a facial-surface identity; the Gregoret summarized definition recovered here uses the incisal edge.
- Critical rule: do **not** substitute facial-surface and incisal-edge variants.
- LOT06: `M_L1_EDGE_APOG_MM_V1`.
- Runtime: **EXECUTABLE** through `RICKETTS_L1_EDGE_APOG_CANONICAL_MM_V2`.
- Geometry: shortest/perpendicular distance from `L1_incisal` to `A-Pog_hard`; sign positive anterior, negative posterior. Frankfort Po→Or is used only to orient the sign, not the magnitude.
- Calibration: required for mm output.
- Profile status: **SOURCE_LOCKED / EXECUTABLE**.

### 9. Lower incisor inclination to A-Pog
- Definition: angle between the long axis of the lower central incisor and `A-Pog`.
- Unit: degrees.
- Historical reference: 22° ± 4°.
- Age behavior: stable in summarized Gregoret material.
- LOT06: `M_RICKETTS_L1_APOG_INCLINATION_DEG_V1`.
- Runtime: **EXECUTABLE** through `RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2`.
- Profile status: **SOURCE_LOCKED / EXECUTABLE**.

### 10. Upper first molar to PTV
- Definition: linear distance from the distal surface of the upper first molar to pterygoid vertical.
- PTV: vertical through the posterior pterygomaxillary reference, perpendicular to Frankfort.
- Unit: mm.
- Historical reference: patient age + 3 mm, ± 3 mm.
- LOT06: `M_U6_PTV_MM_V1`.
- PTV construction: `RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1` — line through explicit `PR_Ricketts_PTV` at the most posterior outline of the pterygo-palatine fossa, perpendicular to anatomical Frankfort `Po_anatomic-Or`.
- Runtime: **PTV CONSTRUCTION EXECUTABLE / MEASUREMENT BLOCKED** because `U6_distal` is not yet a validated canonical runtime identity.
- Critical rule: generic SRPose `PT_point`, `Ptm`, or facial-axis `Pt_Ricketts` are not promoted to `PR_Ricketts_PTV`, and generic `U6` is not promoted to distal-surface authority.
- Profile status: **SOURCE_LOCKED / FAIL_CLOSED_U6_DISTAL_IDENTITY**.

### 11. Lower incisor to occlusal plane (extrusion)
- Definition: distance from the lower incisal edge to the Ricketts functional occlusal plane.
- Unit: mm.
- Historical reference recovered from Gregoret text: +1.25 mm ± 2 mm.
- Independent clinical forms sometimes round this to ~1 mm; Digital Crown must keep the exact source-qualified Gregoret reference.
- LOT06 canonical ID: `M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1`.
- Runtime: **BLOCKED_CONSTRUCTION** because the Ricketts functional occlusal-plane construction/anchors are not yet independently validated.
- Profile status: **SOURCE_LOCKED_MEANING / EXECUTION_BLOCKED**.

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
- Exact executable now: 7 — facial depth, convexity, maxillary depth, L1/A-Pog distance, L1/A-Pog inclination, interincisal angle, lower lip/E-plane.
- Conditional executable: 1 — facial axis.
- Source-locked but identity/construction blocked: 5 — lower facial height, U6/PTV, mandibular plane, lower-incisor extrusion, mandibular arc.
- No remaining Gregoret-13 row lacks a canonical measurement ID; blocked rows remain fail-closed until their exact evidence contracts are validated.

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

Continue the blocked Gregoret-13 evidence contracts **without UI activation**:
1. Represent validated manual/constructed `Xi_Ricketts`, `Pm_Ricketts`, and `DC_Ricketts` evidence before lower-face-height/mandibular-arc runtime execution.
2. Validate the exact Ricketts mandibular-plane tangent contact construction; do not substitute Go-Me.
3. Validate exact Ricketts functional-occlusal anchors before lower-incisor extrusion execution.
4. Resolve explicit U6 distal authority for the U6/PTV measurement.
5. Keep automatic authority fail-closed until independently validated.

Already implemented and source-locked in this branch:
- Ricketts maxillary depth.
- Ricketts lower-incisor A-Pog inclination.

Then tests → two fresh reviews → confirmation → only then UI/report/tracing.

No merge. No deployment.


## A3 execution synchronization — 2026-10-04

Confirmation review detected and corrected a documentation/runtime contradiction:
- Maxillary depth and L1/A-Pog inclination were already executable in code/profile/LOT06 contract but still described above as missing in the source-lock document.
- The execution summary and Next exact have now been synchronized.

This finding was **MAJOR** because stale scientific documentation could misstate canonical authority even when runtime behavior is correct.

After this correction, prior confirmation confidence is invalidated until CI + two reviews + confirmation are rerun on the new HEAD.


## A4 L1 edge–A-Pog binding — 2026-10-04

The Gregoret lower-incisor protrusion row is now bound to the exact canonical identity `M_L1_EDGE_APOG_MM_V1`.

Source-locked semantics:
- point: mandibular incisal edge/tip, not facial crown surface;
- reference: A–Pog hard-tissue line;
- magnitude: shortest/perpendicular distance;
- sign: positive anterior to A–Pog, negative posterior;
- unit: mm with verified calibration;
- Frankfort Po→Or is a computational sign-orientation dependency only and does not alter the distance magnitude.

Runtime method: `RICKETTS_L1_EDGE_APOG_CANONICAL_MM_V2`.

No historical norm/classification is activated by this binding.


## A5 PTV construction contract — 2026-10-04

Primary Ricketts 1981 source defines PTV as a line through a point selected at the most posterior outline of the pterygo-palatine fossa, drawn perpendicular to Frankfort. Table 5 records upper first molar position from PTV and age-linked expected values. Peer-reviewed longitudinal Ricketts work uses the distal point of the maxillary first molar (A6) for this measurement.

Digital Crown contract:
- construction ID: `RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1`;
- required explicit identities: `PR_Ricketts_PTV`, `Po_anatomic`, `Or`;
- generic `PT_point` is rejected as scientific authority;
- construction fails closed for missing, mixed-source or degenerate Frankfort evidence;
- `M_U6_PTV_MM_V1` remains blocked until an explicit `U6_distal` identity is validated; generic SRPose `U6` is not silently substituted.

No age norm or clinical interpretation is activated by this construction.


### A5 correction — PTV landmark identity separation

Adversarial review found a MAJOR identity collision: facial-axis `Pt_Ricketts` is not the same scientific landmark as the PTV reference point described by Ricketts 1981. The PTV contract now requires a distinct explicit landmark `PR_Ricketts_PTV` corresponding to the most posterior outline of the pterygo-palatine fossa. `Pt_Ricketts`, generic `PT_point`, and `Ptm` are all rejected as silent aliases.


## A6 Ricketts mandibular-plane source-lock refinement — 2026-10-05

Source review confirms that the summarized Ricketts mandibular plane is a tangent to the inferior mandibular border joining Me to the lowest point of the mandibular ramus. This is not equivalent to silently reusing the Tweed/DC Go-Me line.

Digital Crown decision:
- canonical measurement ID remains `M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1`;
- generic `M_FH_GOME_DEG_V1` / Go-Me is forbidden as a silent substitute;
- no new automatic landmark identity is introduced;
- execution remains `BLOCKED_CONSTRUCTION` until the exact tangent-contact evidence can be represented by a validated canonical construction/identity contract;
- no norm/classification is activated.

This refinement closes the semantic alias risk but does not make the measurement executable.


## A7 Ricketts functional occlusal plane / lower-incisor extrusion — 2026-10-05

Source synthesis:
- Gregoret summarized Ricketts material defines lower-incisor extrusion as the distance from the lower incisal edge to the occlusal plane, with historical reference +1.25 mm ± 2 mm.
- Ricketts 1981 documents the clinical behavior and orientation of the occlusal plane in relation to the denture/Xi region but does not, in the source material recovered here, provide enough explicit anchor detail to promote a new automatic construction.
- General cephalometric literature distinguishes the functional occlusal plane from an anatomic/incisor-molar plane and describes it through the posterior occlusion (molar/premolar interdigitation). That supporting convention is not sufficient by itself to create Ricketts-specific landmark authority in Digital Crown.

Digital Crown contract:
- measurement ID: `M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1`;
- target point: explicit lower incisal edge `L1_incisal`;
- reference: Ricketts functional occlusal plane;
- unit: mm;
- historical Gregoret reference: +1.25 mm ± 2 mm, reference-display only;
- `M_OCCLUSAL_PLANE_SN_DEG_V1` and any Steiner/Downs/anatomic occlusal-plane construction are forbidden silent substitutes;
- no new molar/premolar landmark authority is introduced by this source-lock;
- runtime remains `BLOCKED_CONSTRUCTION` until the exact Ricketts functional-occlusal anchors/construction are independently validated and versioned.

This slice therefore source-locks meaning and non-substitution rules, not execution.


## A8 Ricketts mandibular arc identity contract — 2026-10-05

The mandibular arc is source-locked as the angle formed by the Ricketts condylar axis `DC_Ricketts-Xi_Ricketts` and the distal extrapolation of the corpus axis `Xi_Ricketts-Pm_Ricketts`, with Xi as the shared construction center.

Source-specific identities:
- `Xi_Ricketts`: geometric center of the ramus; historical construction uses the R1-R4 ramal rectangle;
- `Pm_Ricketts`: protuberance menti / stable suprapogonion of the mandibular symphysis;
- `DC_Ricketts`: bisecting/central point of the condylar neck used by the condylar axis.

Fail-closed rules:
- `DC_Ricketts` is not silently aliased to generic `DC`, `Co`, `Co_anatomic`, or `D_point`;
- `Xi_Ricketts` is not silently aliased to generic `Xi`, `Go`, `Ar`, or `PT_point`;
- `Pm_Ricketts` is not silently aliased to generic `Pm`, `Pog`, `Pog_hard`, `B`, or `Me`;
- no automatic DC/Xi/Pm landmark authority is created in this slice;
- runtime remains `BLOCKED_LANDMARK` until explicit manual/constructed identities are represented by a validated canonical evidence contract.

Contract artifact:
`docs/audits/schemas/ortho_lot08_ricketts_mandibular_arc_identity_contract_v1.json`.

Historical 26° ± 4° is reference-display only. The age-adjustment delta remains quarantined and no VERT/classification authority is activated.
