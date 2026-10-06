# LOT08 — Ricketts DC / mandibular arc source-lock

Date: 2026-10-06
Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`

## Goal

Close the final landmark authority required for the Gregoret-lineage mandibular arc without aliasing generic condylar points.

## Primary source findings

Ricketts 1972 defines `Dc` as a point at the bisection of the condylar neck, taken as high as visible in the cephalometric film below the fossa. The same paper establishes:
- `Dc-Xi` as the repeatable condylar axis;
- `Xi-Pm` as the corpus axis.

Ricketts 1981 describes the mandibular bend/arc as the angulation of the condylar process to the body of the mandible, measured between:
- the condylar axis through Xi and the center of the condylar neck;
- the posterior extension of the corpus axis `Pm-Xi`.

## Digital Crown identity authority

Explicit identity:
- `DC_Ricketts`

Authority:
- `MANUAL` or `MANUAL_CORRECTED` only.

Forbidden aliases:
- `DC`
- `Co`
- `Co_anatomic`
- `D_point`

Digital Crown does not auto-construct `DC_Ricketts` in this lock. The source gives an anatomical/film-selection definition but does not provide a sufficiently deterministic image-processing construction to justify automatic authority.

## Geometry

Measurement:
`M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1`

Method:
`RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2`

Inputs:
- manual/manual-corrected `DC_Ricketts`;
- canonical `Xi_Ricketts` from `RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1`;
- manual/manual-corrected `Pm_Ricketts`.

Rule:
- condylar vector at Xi = `Xi→DC`;
- posterior corpus extension at Xi = direction `Pm→Xi`;
- output = non-reflex angle between those vectors.

All evidence must resolve to the same source image. Degenerate axes are `INVALID`.

## Runtime state

`CONDITIONAL_EXECUTABLE`.

This lock activates geometry only. It does not activate:
- historical age correction;
- sex-specific interpretation;
- VERT;
- universal classification;
- diagnosis, prognosis, treatment recommendation.

The historical age-delta transcription remains quarantined in the identity contract.

## Sources

- Ricketts RM. A principle of arcial growth of the mandible. Angle Orthod. 1972;42(4):368-386. DOI `10.1043/0003-3219(1972)042<0368:APOAGO>2.0.CO;2`.
- Ricketts RM. Perspectives in the clinical application of cephalometrics. Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.
- Kim et al. Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis. Korean J Orthod. 2014;44(2):77-87. Corroborates DC as the bisecting point of the condylar neck and the DC-Xi/Xi-Pm axes.

No UI/report activation. No merge/deployment authorization.
