# LOT08 — Ricketts Atlas/33 Wave C internal-structures source-lock

Date: 2026-10-06
Profile: `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`

## Scope

Wave C covers Atlas factors #26–#33. Historical norms, age/sex correction, VERT classification, diagnosis, prognosis and treatment recommendations remain disabled.

## Source hierarchy

Primary profile authority:
Fernández Sánchez J, Da Silva Filho OG. *Atlas cefalometría y análisis facial*. Ripano, 2009, chapter 13.

Primary historical corroboration:
Ricketts RM. *Perspectives in the clinical application of cephalometrics*. Angle Orthod. 1981;51(2):115–150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

Peer-reviewed measurement corroboration:
Bae EJ, Kwon HJ, Kwon OW. Korean J Orthod. 2014;44(2):77–87. DOI `10.4041/kjod.2014.44.2.77`.

## #26 Cranial deflection

Canonical ID:
`M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1`.

Method:
`RICKETTS_CRANIAL_DEFLECTION_CANONICAL_DEG_V2`.

Definition:
acute/non-oriented angle between anatomical Frankfort `Po_anatomic→Or` and `Ba→N`.

No historical norm is activated.

## #27 Anterior cranial length

Canonical ID:
`M_RICKETTS_ANTERIOR_CRANIAL_LENGTH_CC_N_MM_V1`.

Method:
`RICKETTS_ANTERIOR_CRANIAL_LENGTH_CANONICAL_MM_V2`.

Definition:
linear distance `CC_Ricketts_Atlas2009→N`.

Atlas-specific CC construction:
`RICKETTS_CC_ATLAS2009_BAN_PTGN_INTERSECTION_V1`.

Rule:
intersection of `Ba–N` and the source-locked facial axis `Pt_Ricketts–Gn_constructed_Ricketts`.

Authority:
- `Pt_Ricketts` MANUAL or MANUAL_CORRECTED;
- canonical Ricketts Gn construction;
- same source image;
- verified calibration.

Historical note:
Ricketts 1981 also contains wording describing CC as the point on Ba–N reached by a perpendicular from Pt. The Atlas profile uses the Atlas line-intersection construction and does not silently merge this historical variant.

## #28 Posterior facial height

Canonical ID:
`M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1`.

Method:
`RICKETTS_POSTERIOR_FACIAL_HEIGHT_CANONICAL_MM_V2`.

Definition:
linear distance `GO_Ricketts_PFH→CF_Ricketts`.

`GO_Ricketts_PFH` is a source-specific clinician-controlled Gonion identity:
MANUAL or MANUAL_CORRECTED only.

`CF_Ricketts` must come from `RICKETTS_CF_FH_PTV_INTERSECTION_V1`; generic CF aliases are forbidden.

Verified calibration and same-image evidence are required.

## #29 Total facial height — Atlas transcription conflict resolved

Canonical ID:
`M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1`.

Method:
`RICKETTS_TOTAL_FACIAL_HEIGHT_CANONICAL_DEG_V2`.

Resolved definition:
acute angle between `Ba–N` and `Pm–Xi`.

Why the earlier conflict is resolved:
- the indexed Atlas table duplicates the label “posterior facial height” at row 29 but gives an angular value around 60°;
- row 28 is already the linear posterior facial height `Go–CF`;
- independent comprehensive Ricketts implementations identify the ~60° angular measurement as **Total Facial Height**, `NaBa / PmXi`.

Digital Crown records this as a source transcription/OCR conflict resolved by internal dimensional consistency plus independent Ricketts implementations. It does not rewrite row 28.

Authority:
canonical Xi construction + MANUAL/MANUAL_CORRECTED `Pm_Ricketts`.

## #30 Ramus position

Canonical ID:
`M_RICKETTS_RAMUS_POSITION_FH_CFXI_DEG_V1`.

Method:
`RICKETTS_RAMUS_POSITION_CANONICAL_DEG_V2`.

Definition:
acute angle between anatomical Frankfort and `CF_Ricketts→Xi_Ricketts`.

Both CF and Xi must be canonical constructions.

## #31 Porion location

Canonical ID:
`M_RICKETTS_PORION_LOCATION_PTV_MM_V1`.

Method:
`RICKETTS_PORION_LOCATION_CANONICAL_MM_V2`.

Definition:
signed distance from source-locked PTV to anatomical Porion measured along the canonical Frankfort anterior axis.

Sign:
- Porion anterior to PTV: positive;
- Porion posterior to PTV: negative.

This matches peer-reviewed Ricketts implementations that explicitly interpret posterior Porion as a negative value.

Verified calibration is mandatory.

## #32 Mandibular arc

Existing converged ID:
`M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1`.

No change in Wave C. Existing DC/Xi/Pm source-lock remains authoritative.

## #33 Mandibular body / corpus length

Canonical ID:
`M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1`.

Method:
`RICKETTS_CORPUS_LENGTH_CANONICAL_MM_V2`.

Definition:
straight-line distance `Xi_Ricketts→Pm_Ricketts`.

Authority:
canonical Xi construction + MANUAL/MANUAL_CORRECTED Pm + same source image + verified calibration.

## Facad boundary

Facad `Ricketts (32 F)` / `Ricketts (13 F)` remain parity-only targets until direct Facad trace/export observation. No equivalence is inferred from vendor labels.
