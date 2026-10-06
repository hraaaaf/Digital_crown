# LOT08 — Ricketts Xi / Pm / lower facial height source-lock

Date: 2026-10-06
Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`

## Goal

Close the landmark authority for the Ricketts lower facial height without silently aliasing generic mandibular points.

## Primary source findings

Ricketts 1972 describes Xi as the centroid of the mandibular ramus obtained from four ramal reference points: R1 at the deepest subcoronoid incisure, R2 directly opposite on the posterior ramal border, R3 at the depth of the sigmoid notch, and R4 directly inferior on the lower border. The four limits form a rectangle; Xi is obtained at its center.

Ricketts 1981 reiterates Xi at the center of the ramus and defines protuberance menti (Pm) as the recessive area above pogonion. Xi joined to Pm forms the corpus axis. The oral gnomon/lower facial height is the angle ANS-Xi-Pm with vertex at Xi.

## Digital Crown identities

Explicit source identities:
- `R1_Ricketts`
- `R2_Ricketts`
- `R3_Ricketts`
- `R4_Ricketts`
- `Pm_Ricketts`

Anatomical orientation identities:
- `Po_anatomic`
- `Or`

Constructed output:
- `Xi_Ricketts`

Construction ID:
- `RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1`

## Construction rule

The ramal rectangle is expressed in the anatomical Frankfort basis so the result does not depend on display rotation or mirroring.

- R1/R2 provide the opposed limits along the Frankfort axis.
- R3/R4 provide the superior/inferior limits along the perpendicular axis.
- Xi is reconstructed from the midpoint of those two coordinate intervals.

All evidence must come from one source image. Degenerate Frankfort or a collapsed rectangle returns `INVALID`.

## Pm authority

`Pm_Ricketts` remains an explicit anatomical landmark. Digital Crown does not infer it from `Pog_hard`, `B`, `Me`, or any generic `Pm` label.

## Lower facial height

Measurement:
`M_ORAL_GNOMON_ANS_XI_PM_DEG_V1`

Method:
`RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2`

Definition:
non-reflex angle between vectors Xi→ANS and Xi→Pm_Ricketts.

State:
`CONDITIONAL_EXECUTABLE`.

Gate:
- valid canonical Xi construction;
- explicit `ANS`;
- explicit `Pm_Ricketts`;
- same source image.

No historical norm, age correction, facial-type classification, VERT score, diagnosis, prognosis, or treatment implication is activated.

## Mandibular arc impact

The Xi side of the mandibular arc is now source-locked. The full arc remains `BLOCKED_LANDMARK` because `DC_Ricketts` is not yet runtime-authoritative.

## Sources

- Ricketts RM. A principle of arcial growth of the mandible. Angle Orthod. 1972;42(4):368-386. DOI `10.1043/0003-3219(1972)042<0368:APOAGO>2.0.CO;2`. Primary Xi construction figure/text.
- Ricketts RM. Perspectives in the clinical application of cephalometrics. Angle Orthod. 1981;51(2):115-150. Xi center of ramus, Pm above pogonion, Xi-Pm corpus axis, ANS-Xi-Pm oral gnomon.
- Later peer-reviewed literature is used only to corroborate the R1-R4 rectangle and ANS-Xi-Pm geometry; it does not replace the primary source contract.

No UI/report activation. No merge/deployment authorization.
