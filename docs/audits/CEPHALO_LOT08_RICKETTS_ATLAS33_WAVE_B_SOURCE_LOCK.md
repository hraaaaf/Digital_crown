# LOT08 — Ricketts Atlas/33 Wave B source-lock

Date: 2026-10-06
Profile: `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`

## Scope

Wave B covers Atlas factors #14, #15, #17, #18, #21, #23 and #24.

No historical norm, age correction, VERT classification, diagnosis, prognosis or treatment recommendation is activated.

## Source authority

Primary profile authority:
Fernández Sánchez J, Da Silva Filho OG. *Atlas cefalometría y análisis facial*. Ripano, 2009. Chapter 13, Ricketts analysis.

Corroboration:
- Ricketts RM. *Perspectives in the clinical application of cephalometrics*. Angle Orthod. 1981;51(2):115-150. CF is the intersection of true Frankfort with the pterygoid-root vertical (PTV).
- Peer-reviewed Ricketts implementations describe facial taper as mandibular plane vs N-Pog, maxillary height as N-CF-A, and palatal plane vs Frankfort.

## #14 — Occlusal-plane distance to Xi

Canonical ID:
`M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1`.

Atlas definition:
linear distance from Xi to the functional occlusal plane.

The Atlas/reference material describes clinical positive/negative values, but this pass did not recover a source-defined geometric rule that orients the FOP normal independently of screen orientation.

State:
`SOURCE_LOCKED_DEFINITION__SIGN_ORIENTATION_BLOCKED`.

No runtime method is activated.

## #15 — Occlusal-plane inclination

Canonical ID:
`M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1`.

Method:
`RICKETTS_OCCLUSAL_PLANE_XIPM_CANONICAL_DEG_V2`.

Definition:
acute/non-oriented angle between:
- source-locked Ricketts functional occlusal plane;
- mandibular corpus axis `Xi_Ricketts→Pm_Ricketts`.

Required authority:
- canonical Xi construction only;
- `Pm_Ricketts` MANUAL or MANUAL_CORRECTED;
- canonical FOP construction;
- same source image.

## #17 — Upper-lip length

Canonical ID:
`M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1`.

Method:
`RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2`.

Atlas definition:
straight-line distance between anterior nasal spine (ANS/ENA) and the labial commissure.

Digital Crown identity:
`LABIAL_COMMISSURE_Ricketts` must be MANUAL or MANUAL_CORRECTED.

Generic `Em`, Stomion, upper-lip vermilion points and generic mouth-center identities are not silently substituted.

Verified calibration and same-image evidence are required.

## #18 — Labial commissure to occlusal plane

Canonical ID:
`M_RICKETTS_COMMISSURE_FOP_MM_V1`.

Atlas definition:
distance from labial commissure to the occlusal plane. Atlas text states negative values when the occlusal plane passes below the commissure and positive values for the inverse relation.

State:
`SOURCE_LOCKED_DEFINITION__SIGNED_NORMAL_ORIENTATION_BLOCKED`.

Reason:
the clinical sign is described, but an orientation rule for the FOP normal that is invariant to image rotation/mirroring is not explicitly source-defined. No runtime method is activated.

## #21 — Facial taper / cone

Canonical ID:
`M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1`.

Method:
`RICKETTS_FACIAL_TAPER_CANONICAL_DEG_V2`.

Definition:
acute angle between:
- facial plane `N→Pog_hard`;
- source-locked Ricketts mandibular plane.

The mandibular plane must come from `RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1`; generic Go-Me/Tweed substitution is forbidden.

## #23 — Maxillary height

Canonical ID:
`M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1`.

Method:
`RICKETTS_MAXILLARY_HEIGHT_CANONICAL_DEG_V2`.

Definition:
angle `N-CF-A`, vertex at CF.

CF construction:
`RICKETTS_CF_FH_PTV_INTERSECTION_V1`.

CF is constructed only as the intersection of:
- anatomical Frankfort;
- source-locked Ricketts PTV.

Because PTV requires manual/manual-corrected `PR_Ricketts_PTV`, maxillary height inherits that authority gate.

No generic CF point is accepted.

## #24 — Palatal plane to Frankfort

Canonical ID:
`M_RICKETTS_PALATAL_PLANE_FH_DEG_V1`.

Method:
`RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2`.

Definition:
acute angle between:
- anatomical Frankfort `Po_anatomic→Or`;
- Ricketts palatal plane `ANS→PNS_Ricketts`.

`PNS_Ricketts` must be MANUAL or MANUAL_CORRECTED. Generic/automatic PNS is not promoted silently.

## Compatibility boundary

Facad `Ricketts (32 F)` and `Ricketts (13 F)` remain parity targets only. No row-membership or sign equivalence is inferred from the vendor labels.
