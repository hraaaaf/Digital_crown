# LOT08 — Ricketts Protocol Evidence Manifest — A0

Date: 2026-10-04  
Branch: `feat/ortho-studio-lot08-ricketts-protocol`  
Base: `master@19a91889b8b60ea97e49f717909be9cc83fdf919`

## Goal
Converge the Ricketts protocol as the next non-closed LOT08 protocol without silently relabeling generic Digital Crown geometry as historical Ricketts geometry.

## Gate state
- `ORTHO_ANALYSIS_PROTOCOLS_SOURCE_LOCKED / RICKETTS`: OPEN.
- `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED / RICKETTS`: OPEN.
- No product implementation is authorized by this A0 document.

## External evidence baseline

### Primary lineage
1. Ricketts RM. *A foundation for cephalometric communication*. Am J Orthod. 1960;46:330-357. DOI: 10.1016/0002-9416(60)90047-6.
2. Ricketts RM. *Perspectives in the clinical application of cephalometrics. The first fifty years*. Angle Orthod. 1981;51(2):115-150. DOI: 10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2. PMID: 6942666.

The 1960 primary source explicitly describes a five-measure communication system:
1. facial angle;
2. XY axis angle;
3. measure of contour;
4. upper incisor relationship to the A-Po plane;
5. lower incisor relationship to the A-Po plane.

It separately proposes a deeper structural analysis rather than defining one timeless universal "complete Ricketts" package.

### Independent longitudinal implementation
Bae EJ, Kwon HJ, Kwon OW. *Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis*. Korean J Orthod. 2014;44(2):77-87. DOI: 10.4041/kjod.2014.44.2.77. PMCID: PMC3971129.

Observed study contract:
- 31 subjects with normal occlusion followed from age 9 to 19;
- 6 serial lateral cephalograms per participant at two-year intervals;
- landmarks include PT, DC, CC, CF, XI and PM in addition to conventional hard-tissue and dental landmarks;
- several Ricketts measurements vary with age and some show sex-dependent growth;
- therefore these norms are population/age/sex scoped, not universal.

This study is an independent implementation/reference set. It must not be silently treated as the normative definition of the 1960 or 1981 primary publications.

## Repo baseline on current master

The current canonical completeness audit still states that Ricketts cannot be reduced to the E-line and lists major gaps in active authority/UI.

### Existing source-aware / canonical-v2 capability
- Facial depth.
- Maxillary convexity.
- E-line Ls.
- E-line Li.
- Facial axis geometry with explicit `Pt_Ricketts` and a constructed Ricketts Gn dependency.
- Explicit fail-closed behavior when `Pt_Ricketts` is unavailable.
- Source-specific distinction between Ricketts facial depth and Downs facial angle.

### Still not enough for LOT08 closeout
The current audit identifies unresolved or non-promoted Ricketts families including:
- mandibular plane / FH under Ricketts-specific convention;
- lower facial height;
- maxillary depth;
- mandibular arc;
- corpus length;
- lower incisor to A-Pog distance;
- lower incisor to A-Pog inclination;
- overjet / overbite under source-specific definitions;
- upper first molar to PTV;
- internal-structure measures requiring Xi/Pm/CF/DC and related constructions.

Therefore the presence of Ricketts-labelled measurements in LOT06 is not evidence that LOT08 Ricketts is complete.

## Protocol identity decision

A single profile named simply `RICKETTS_V1` or `RICKETTS_CLINICAL_PROFILE_1981_V1` is rejected at A0 because it would collapse historically distinct scopes.

LOT08 must model Ricketts as explicit variants.

### Variant A — communication profile
Provisional protocol ID:
`RICKETTS_COMMUNICATION_1960_PROTOCOL_V1`

Composition authority:
Ricketts 1960 five-measure communication system.

Status:
COMPOSITION SOURCE-IDENTIFIED, but NOT SOURCE-LOCKED FOR IMPLEMENTATION until the exact geometric definitions/conventions of each of the five measures are captured claim-by-claim from an authoritative source.

### Variant B — later structural/clinical profiles
The 1981 publication and later implementations represent broader clinical use and structural analysis.

Status:
SEPARATE FUTURE VERSIONED PROFILE(S). Do not merge into Variant A.

### Normative/reference profiles
The 2014 Korean longitudinal values are a population-specific reference set, not a universal Ricketts norm profile.

Any future norm-set ID must encode population/age/sex applicability and fail closed outside its declared scope.

## Required source-lock contract

For every selected measure:
`protocol measurement ID → canonical LOT06 measurement ID → exact source definition → landmarks → construction → unit → calibration requirement → norm set → applicability → availability behavior → UI row → tracing geometry → report section`.

Any measure without this chain remains excluded or explicitly NOT_COMPUTABLE. No fallback geometry.

## Known blockers at A0
1. The exact geometric definitions for all five 1960 communication measures are not yet frozen claim-by-claim in this LOT08 manifest.
2. `Pt_Ricketts`: explicit identity exists, but automatic legacy `PT_point` cannot be promoted by name alone.
3. `Xi`, `Pm`, `CF`, `DC`: not available as validated runtime identities in the current detector contract.
4. Ricketts mandibular plane / FH cannot inherit generic Tweed/Downs FMA semantics.
5. PTV and U6-to-PTV require an exact source-specific construction.
6. Age/sex/population-dependent normative values must not become universal classifications.
7. Active UI/report completeness for the Ricketts family is not yet demonstrated.
8. LOT06's provisional `RICKETTS_V1` dependency pack must not be reinterpreted as the final LOT08 protocol profile without an explicit versioned mapping.

## Adversarial review A — orthodontic source fidelity
Finding: MAJOR in the first draft. The proposed `RICKETTS_CLINICAL_PROFILE_1981_V1` over-compressed distinct historical scopes and risked using the 2014 Korean implementation as implicit support for a universal Ricketts profile.

Correction:
- split 1960 communication profile from later structural/clinical profiles;
- keep 2014 as population-specific independent reference;
- forbid universal norm inheritance.

Post-correction score: 9.2/10.
Status: no remaining BLOCKER/MAJOR in the A0 framing, but source-lock remains OPEN because exact measure definitions are not yet fully captured.

## Adversarial review B — architecture / canonical authority
Finding: MAJOR in the first draft. Existing LOT06 `RICKETTS_V1` is a provisional dependency pack, not proof of a final LOT08 clinical protocol. Reusing that identifier as the final profile would create authority drift between engine coverage and product protocol semantics.

Correction:
- introduce a distinct protocol-level identity `RICKETTS_COMMUNICATION_1960_PROTOCOL_V1`;
- require explicit canonical LOT06 mapping per measure;
- preserve existing fail-closed landmark/construction semantics;
- no UI/report activation until the protocol profile is source-locked.

Post-correction score: 9.3/10.
Status: no remaining BLOCKER/MAJOR in the A0 architecture framing.

## Confirmation review
A0 framing re-reviewed after both corrections:
- no new BLOCKER;
- no new MAJOR;
- one intentional open scientific gate remains: exact definition/construction lock for each selected 1960 measure.

This means A0 documentation converged, not the Ricketts protocol itself.

## A0 verdict
Ricketts is the first non-converged LOT08 protocol after Steiner and Tweed-Merrifield.

`RICKETTS_SOURCE_LOCK = NOT_SATISFIED`.

The next safe action is source extraction/mapping, not product implementation.

## Next exact
1. Freeze the five 1960 communication measures claim-by-claim.
2. Map each to current LOT06 registry and runtime identity support.
3. Classify each row: EXECUTABLE / MANUAL_IDENTITY_REQUIRED / NEW_CONSTRUCTION_REQUIRED / NEW_LANDMARK_REQUIRED / NORM_QUARANTINED / EXCLUDED.
4. Only when the five-measure profile is fully source-locked may code/UI/report implementation start.
5. Later structural Ricketts profiles remain separate and versioned.

No merge. No deployment.
