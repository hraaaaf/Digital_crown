# LOT08 — Ricketts Atlas/33 Wave A dental source-lock

Date: 2026-10-06
Profile target: `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`

## Scope

This contract source-locks the dental Wave A factors carried by the published complete Ricketts implementations:
1. molar relationship;
2. canine relationship;
3. incisor overjet;
4. incisor overbite;
10. lower-incisor protrusion;
11. upper-incisor protrusion;
13. upper-incisor inclination.

It does not activate historical norms, age corrections, diagnosis, prognosis, VERT, or treatment recommendations.

## Source hierarchy and recovered semantics

### Ricketts 1981 — primary clinical authority
Robert M. Ricketts, *Perspectives in the clinical application of cephalometrics. The first fifty years*, Angle Orthodontist 1981;51(2):115-150, DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

The paper explicitly treats the denture in horizontal and vertical directions, identifies A-Po as the practical basis for lower-incisor sagittal position, and describes the upper first molar from PTV. It supports Ricketts-specific denture geometry but does not, in the recovered pages, provide every Wave A row definition.

### Peer-reviewed Ricketts implementation — Kim et al. 2014
Kim et al., Korean J Orthod. 2014;44(2):77-87, DOI `10.4041/kjod.2014.44.2.77`, PMCID `PMC3971129`.

The published measurement set explicitly includes:
- molar relationship;
- incisor overjet;
- incisor overbite;
- lower-incisor tip (B1) to A-Po;
- upper-incisor tip (A1) to A-Po;
- B1 and A1 inclination to A-Po.

This corroborates incisal-tip rather than facial-surface semantics for Ricketts lower-incisor protrusion.

### Cephalometric interoperability mapping / complete-analysis manuals
The recovered Ricketts variable definitions describe:
- molar relationship = separation of distal surfaces of lower and upper permanent first molars measured along the occlusal plane;
- canine relationship = separation of upper/lower canine cusp centers measured along the occlusal plane;
- overjet = separation of upper/lower incisal edges measured at the occlusal-plane level;
- overbite = incisal-edge separation measured perpendicular to the occlusal plane.

These are used only where they agree with the published Ricketts measurement set; they do not authorize norms.

## Canonical identities and execution

### #1 Molar relationship
ID: `M_RICKETTS_MOLAR_RELATION_FOP_MM_V1`

Required:
- `L6_DISTAL_Ricketts`: MANUAL or MANUAL_CORRECTED;
- `U6_DISTAL_Ricketts`: MANUAL or MANUAL_CORRECTED;
- source-locked `RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1`;
- verified calibration;
- same source image.

Rule:
project `L6_DISTAL_Ricketts - U6_DISTAL_Ricketts` on the canonical FOP direction `premolar→molar` (posterior-positive). A lower molar located mesially/anteriorly to the upper therefore produces a negative value.

Generic molar centers, cusp tips, mesial surfaces and generic `U6/L6` labels are forbidden.

### #2 Canine relationship
ID: `M_RICKETTS_CANINE_RELATION_FOP_MM_V1`

Required:
- `L3_CUSP_Ricketts`: MANUAL or MANUAL_CORRECTED;
- `U3_CUSP_Ricketts`: MANUAL or MANUAL_CORRECTED;
- source-locked FOP;
- verified calibration;
- same source image.

Rule:
project `L3_CUSP_Ricketts - U3_CUSP_Ricketts` on posterior-positive FOP. Lower canine mesial/anterior to upper is negative.

### #3 Overjet
ID: `M_RICKETTS_OVERJET_FOP_MM_V1`

Required:
- `L1_incisal`;
- `U1_incisal`;
- source-locked FOP;
- verified calibration;
- same source image.

Rule:
project `L1_incisal - U1_incisal` on posterior-positive FOP. Upper incisor anterior to lower yields positive overjet.

This is not promoted from generic `M_OVERJET_MM_V1`; the Ricketts FOP convention has its own canonical ID.

### #4 Overbite
ID reserved: `M_RICKETTS_OVERBITE_FOP_MM_V1`

Recovered definition: incisal-edge separation perpendicular to the occlusal plane.

State: `SOURCE_LOCKED_DEFINITION__SIGN_ORIENTATION_BLOCKED`.

Reason:
the sources recovered in this pass do not provide enough deterministic information to orient the perpendicular sign independently of screen orientation without importing a Digital Crown convention. No runtime method is activated.

### #10 Lower-incisor protrusion
Canonical ID:
`M_L1_EDGE_APOG_MM_V1`.

Ricketts uses the lower incisal edge/tip relative to A-Pog. The previous matrix mapping to `M_L1_FACIAL_SURFACE_APOG_MM_V1` mixed in a McNamara facial-surface identity and is rejected.

Wave D resolves the direction: cephalometric interoperability mapping specifies the incisal-edge distance perpendicular to A-Pog, while Ricketts primary material and later reviews establish anterior positioning as positive. Runtime uses the existing perpendicular A-Pog construction with Frankfort only to orient anterior/posterior.

### #11 Upper-incisor protrusion
Canonical ID:
`M_RICKETTS_U1_APOG_PROTRUSION_MM_V1`.

Required identities:
`U1_incisal`, A, `Pog_hard`, anatomical Frankfort, verified calibration.

Wave D resolves the direction as the perpendicular distance from the upper incisal tip to A-Pog, positive when the incisal edge is anterior to A-Pog. Modern cephalometric reproducibility literature and Ricketts incisor-position reviews corroborate this construction; no occlusal-plane projection is used.

### #13 Upper-incisor inclination
ID: `M_RICKETTS_U1_APOG_INCLINATION_DEG_V1`.

Required:
`U1_incisal`, `U1_apex`, A, `Pog_hard`.

Rule:
acute line angle between the U1 long axis and A-Pog. No norm/classification is activated.

## Compatibility boundary

Facad `Ricketts (32 F)` / `Ricketts (13 F)` remain compatibility targets. This source-lock does not assert that Facad uses these exact IDs, signs, row membership, or export labels until a Facad trace/export is observed directly.
