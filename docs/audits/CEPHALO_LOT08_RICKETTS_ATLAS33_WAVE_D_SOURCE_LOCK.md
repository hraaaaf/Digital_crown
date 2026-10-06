# LOT08 — Ricketts Atlas/33 Wave D quarantine resolution

Date: 2026-10-06
Profile: `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`

## Goal

Re-open only the six Atlas/33 contracts that remained `SOURCE_LOCKED_BLOCKED` after Waves A–C:
#4 overbite, #10 lower-incisor protrusion, #11 upper-incisor protrusion, #14 occlusal-plane/Xi distance, #18 labial-commissure/occlusal-plane distance, #24 palatal-plane inclination.

Rule: no screen-coordinate convention, mirror-sensitive shortcut, or Digital Crown-only sign rule may be introduced.

## Sources

Primary / near-primary:
- Ricketts RM. *Perspectives in the clinical application of cephalometrics*. Angle Orthod. 1981;51(2):115–150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.
- Fernández Sánchez J, Da Silva Filho OG. *Atlas cefalometría y análisis facial*. Ripano, 2009, chapter 13.
- Cephalometric interoperability/LOINC mapping (2010): Ricketts lower-incisor protrusion is the incisal-edge distance perpendicular to A-Pog; Ricketts overbite is the incisal-tip distance perpendicular to the occlusal plane.

Independent corroboration:
- Sangalli et al. systematic review of incisor positioning: Ricketts relates upper and lower incisors to A-Pog.
- Reproducibility literature defines both U1→A-Pog and L1→A-Pog as perpendicular point-to-line distances.
- Published Ricketts datasets use negative overbite for anterior open bite.
- Atlas text explicitly states #14 positive when the occlusal plane is above Xi and negative when below.
- Atlas text explicitly states #18 negative when the occlusal plane passes below the labial commissure, inverse relation positive.
- Atlas text defines #24 as a directional palatal-plane/Frankfort angle; increased values describe anterior convergence.

## #10 — lower-incisor protrusion: RESOLVED

Canonical:
`M_L1_EDGE_APOG_MM_V1`.

Geometry:
shortest perpendicular distance from `L1_incisal` to line A–Pog.

Sign:
positive anterior to A-Pog, negative posterior.

Runtime:
existing `RICKETTS_L1_EDGE_APOG_CANONICAL_MM_V2`.

Required:
`L1_incisal`, A, `Pog_hard`, anatomical Frankfort for anterior/posterior sign, verified calibration.

The McNamara facial-surface identity remains forbidden for this Ricketts row.

## #11 — upper-incisor protrusion: RESOLVED

Canonical:
`M_RICKETTS_U1_APOG_PROTRUSION_MM_V1`.

Method:
`RICKETTS_U1_APOG_PROTRUSION_CANONICAL_MM_V2`.

Geometry:
shortest perpendicular distance from `U1_incisal` to line A–Pog.

Sign:
positive anterior to A-Pog, negative posterior.

Required:
`U1_incisal`, A, `Pog_hard`, anatomical Frankfort, verified calibration, same source image.

No projection along the occlusal plane is used.

## #4 — overbite: SOURCE SIGN KNOWN / RUNTIME STILL BLOCKED

Canonical:
`M_RICKETTS_OVERBITE_FOP_MM_V1`.

Source geometry:
distance between upper and lower incisal tips measured perpendicular to the functional occlusal plane.

Source sign:
published Ricketts datasets encode anterior open bite with negative overbite; positive values represent vertical overlap.

Remaining blocker:
the current `LandmarkEvidence` / `ConstructionEvidence` model does not carry an explicit anatomical superior/inferior image axis. A signed perpendicular to FOP can therefore flip under image mirroring if derived only from raw screen coordinates.

State:
`SOURCE_SIGN_KNOWN__SUPERIOR_INFERIOR_IMAGE_AXIS_UNAVAILABLE`.

No runtime method is activated.

## #14 — occlusal plane to Xi: SOURCE SIGN KNOWN / RUNTIME STILL BLOCKED

Canonical:
`M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1`.

Source sign:
positive when the occlusal plane passes above Xi; negative when it passes below Xi.

Remaining blocker:
same missing anatomically evidenced superior/inferior image axis.

No screen-Y assumption is allowed.

## #18 — labial commissure to occlusal plane: SOURCE SIGN KNOWN / RUNTIME STILL BLOCKED

Canonical:
`M_RICKETTS_COMMISSURE_FOP_MM_V1`.

Source sign from Atlas:
negative when the occlusal plane passes below the labial commissure; inverse relation positive.

Remaining blocker:
same missing anatomically evidenced superior/inferior image axis.

The source sign is no longer uncertain; only the computational orientation evidence is missing.

## #24 — palatal-plane inclination: SOURCE DIRECTION KNOWN / RUNTIME STILL BLOCKED

Canonical:
`M_RICKETTS_PALATAL_PLANE_FH_DEG_V1`.

Source geometry:
directional angle between anatomical Frankfort and palatal plane ANS–PNS.

Atlas interpretation:
higher values describe anterior convergence; lower values posterior convergence.

Remaining blocker:
a signed two-dimensional angle changes sign under mirroring unless image handedness / superior-inferior orientation is explicitly evidenced. Current cephalo evidence does not carry that orientation contract.

An unsigned acute angle is forbidden because it destroys the clinically meaningful direction.

## Wave D result

Resolved to executable:
- #10 lower-incisor protrusion;
- #11 upper-incisor protrusion.

Remain intentionally blocked:
- #4 overbite;
- #14 FOP/Xi;
- #18 commissure/FOP;
- #24 palatal-plane signed inclination.

These four are no longer blocked for missing scientific sign definitions. They are blocked because the current image evidence contract cannot prove anatomical superior/inferior orientation without adding a non-source convention.

## Next scientific/architecture gate

To unlock the remaining four, add a versioned image-orientation evidence contract that proves anatomical anterior/posterior and superior/inferior handedness from acquisition metadata or another source-authorized reference. Only after that evidence exists should signed FOP-normal and palatal-plane methods be materialized.
