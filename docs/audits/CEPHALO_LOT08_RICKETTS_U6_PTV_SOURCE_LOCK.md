# LOT08 — Ricketts U6 distal / PTV source-lock

Date: 2026-10-06
Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`

## Goal

Close `M_U6_PTV_MM_V1` without silently substituting a generic molar landmark or an implicit screen vertical.

## Source findings

Ricketts 1981 defines the Pterygoid Root Vertical (PTV) as a line drawn perpendicular to Frankfort from a selected point `PR` at the most posterior outline of the pterygo-palatine fossa. The same source uses upper first molar position from PTV as the sagittal molar-position measurement.

Published Ricketts implementations identify A6/U6 as the distal reference of the upper first molar; later peer-reviewed descriptions explicitly label A6 as the upper first molar distal.

## Digital Crown identities

Explicit clinician-controlled identities:
- `PR_Ricketts_PTV` — `MANUAL` or `MANUAL_CORRECTED` only.
- `U6_DISTAL_Ricketts` — `MANUAL` or `MANUAL_CORRECTED` only.

Anatomical Frankfort:
- `Po_anatomic`
- `Or`

Forbidden aliases:
- generic `PTV`, `Pt`, `PT_point`, `Ptm`;
- generic `U6`, cusp-tip U6, centroid U6, mesial surface U6.

## PTV construction

Construction ID:
`RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1`

Rule:
- point = `PR_Ricketts_PTV`;
- direction = perpendicular to anatomical Frankfort `Po_anatomic→Or`;
- all required evidence must come from one source image;
- degenerate Frankfort => `INVALID`;
- non-manual PR authority => `NOT_COMPUTABLE`.

## U6→PTV measurement

Measurement:
`M_U6_PTV_MM_V1`

Method:
`RICKETTS_U6_PTV_CANONICAL_MM_V2`

Numerical rule:
- signed distance is the projection of `PR→U6_DISTAL_Ricketts` on anatomical Frankfort;
- positive = anterior to PTV in the anatomical `Po→Or` direction;
- negative = posterior to PTV;
- verified mm/px calibration is mandatory.

This realizes the geometric distance to a line perpendicular to Frankfort without using screen X/Y, so rotation or horizontal mirroring does not change the clinical sign.

## Runtime state

`CONDITIONAL_EXECUTABLE`.

No historical age norm, population classification, diagnosis, prognosis, or treatment recommendation is activated by this geometry lock.

## Sources

- Ricketts RM. Perspectives in the clinical application of cephalometrics. Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`. PTV definition and upper-first-molar position from PTV.
- Kim et al. Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis. Korean J Orthod. 2014;44(2):77-87. PMCID `PMC3971129`. Corroborates A6 as upper first molar distal in a peer-reviewed Ricketts implementation.

No UI/report activation. No merge/deployment authorization.
