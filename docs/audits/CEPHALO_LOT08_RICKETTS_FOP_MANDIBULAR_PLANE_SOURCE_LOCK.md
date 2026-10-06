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

### Measurement state

`M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1` remains fail-closed.

Reason:
the plane construction is now source-locked, but Digital Crown has not yet frozen a source-specific sign convention for lower-incisor extrusion that preserves the historical positive/negative interpretation. The software therefore does not emit the clinical measurement yet.

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

## Gate result

- Functional occlusal plane construction: SOURCE_LOCKED.
- Lower-incisor extrusion measurement: BLOCKED_SIGN_CONVENTION + explicit anchor availability.
- Ricketts mandibular plane construction: SOURCE_LOCKED.
- MP–FH geometry: CONDITIONAL_EXECUTABLE with explicit `MP_ANGLE_INFERIOR_Ricketts`.

No UI/report activation. No merge/deployment authorization.
