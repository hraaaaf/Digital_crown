# LOT08 — Ricketts functional occlusal plane + mandibular plane source-lock

Date: 2026-10-06  
Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`

## Goal

Resolve two blocked constructions in `RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1` without silently reusing generic/Tweed identities:

1. Ricketts functional occlusal plane used by lower-incisor extrusion.
2. Ricketts mandibular plane used by MP–FH.

## Source lock — functional occlusal plane

### Source evidence

- JCO interview with Robert Schulhof / Rocky Mountain Data Systems (1975), explicitly describing the Ricketts system: the occlusal plane is defined by the bicuspids and molars, not the incisors.
- Peer-reviewed later cephalometric literature consistently defines the functional occlusal plane as the posterior occlusal plane through premolar and molar intercuspation/occlusion.

### Digital Crown construction

Definition ID:
`RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1`

Required explicit manual identities:
- `FOP_PREMOLAR_Ricketts`
- `FOP_MOLAR_Ricketts`

Construction:
a line through the explicit Ricketts premolar-occlusion and molar-occlusion points.

Safety rule:
generic incisors, generic occlusal anchors, or a Steiner/Downs occlusal plane are never substituted.

### Lower-incisor extrusion sign lock

Measurement:
`M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1`

Observed source semantics:
- Ricketts teaching material defines the measurement as the distance from the functional occlusal plane to the lower-incisor edge and reports a positive clinical norm around +1.2/+1.25 mm.
- The same teaching lineage interprets increased values as lower-incisor supraocclusion/extrusion and reduced values as open-bite direction.
- Peer-reviewed Ricketts tables preserve the positive norm and demonstrate that negative patient values are representable, supporting a signed rather than absolute-distance contract.

Digital Crown sign convention:
- magnitude = perpendicular shortest distance from `L1_incisal` to the source-locked Ricketts functional occlusal plane;
- positive = crownward/incisal side of the plane (greater extrusion / supraocclusion);
- negative = apical side of the plane (reduced extrusion / open-bite direction);
- the plane normal is oriented by the anatomical lower-incisor axis `L1_apex → L1_incisal`, never by screen Y or image handedness;
- if the L1 axis is degenerate or effectively parallel to the FOP such that the normal cannot be oriented deterministically, the measurement is `INVALID`;
- verified mm/px calibration is mandatory.

This deterministic orientation is an implementation rule that realizes the documented clinical sign semantics while remaining invariant to image rotation and horizontal mirroring. It is not presented as an additional historical Ricketts landmark construction.

### Measurement state

`M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1` is `CONDITIONAL_EXECUTABLE`.

Required evidence:
- `FOP_PREMOLAR_Ricketts`;
- `FOP_MOLAR_Ricketts`;
- `L1_incisal`;
- `L1_apex`;
- verified calibration;
- all geometric evidence from the same source image.

No historical norm classification is activated by executing the geometry.

## Source lock — mandibular plane

### Source evidence

Ricketts' 1981 clinical-cephalometric discussion states that the commonly useful lower-border definition uses the inferior border of the mandibular angle and Menton at the midline of the symphysis, following the Downs lower-border convention. Later Ricketts implementations report MP–FH as the mandibular-plane inclination.

### Digital Crown construction

Definition ID:
`RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1`

Required explicit identities:
- `MP_ANGLE_INFERIOR_Ricketts` — source-specific inferior mandibular-angle point used by this plane.
- `Me` — Menton.

Construction:
line `MP_ANGLE_INFERIOR_Ricketts → Me`.

Measurement:
`M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1` =
non-reflex angle between anatomical Frankfort `Po_anatomic → Or` and the explicit Ricketts mandibular plane.

Safety rule:
generic `Go`, Tweed FMA, generic `Go-Me`, or `Go-Gn` are not promoted silently to the Ricketts method. If `MP_ANGLE_INFERIOR_Ricketts` is absent, the result is `NOT_COMPUTABLE`.

## Applicability / norms

No population norm, age correction, VERT score, diagnosis, prognosis, or treatment implication is activated by this source-lock. Historical values remain reference-only under the existing LOT08 Ricketts normative policy.

## Evidence references

- Ricketts RM. Perspectives in the clinical application of cephalometrics. Angle Orthod. 1981;51(2):115-150. DOI 10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2.
- Gottlieb EL, Schulhof R. JCO Visits Rocky Mountain Data Systems. J Clin Orthod. 1975;9(12):776 et seq.
- Later peer-reviewed functional-occlusal-plane literature used only to corroborate the posterior premolar/molar construction; it is not allowed to overwrite the Ricketts-specific profile contract.
- Vera-Guerra et al. *Case Reports in Dentistry* (2019), DOI `10.1155/2019/7638959`: Ricketts table reports mandibular-incisor extrusion norm `1.2 ± 2.0 mm` and a negative final value (`-0.1 mm`), confirming signed values are representable.
- Ricketts teaching/manual lineage cross-check: lower-incisor extrusion is measured from the occlusal plane to the lower-incisor edge; increased values are described as supraocclusion and reduced values as open-bite direction. This secondary evidence is used for sign semantics only, not for population norms.

## Gate result

- Functional occlusal plane construction: SOURCE_LOCKED.
- Lower-incisor extrusion measurement: CONDITIONAL_EXECUTABLE with `CROWNWARD_POSITIVE_SIGN_V1`, explicit FOP anchors, explicit L1 axis, same-image evidence and verified calibration.
- Ricketts mandibular plane construction: SOURCE_LOCKED.
- MP–FH geometry: CONDITIONAL_EXECUTABLE with explicit `MP_ANGLE_INFERIOR_Ricketts`.

No UI/report activation. No merge/deployment authorization.
