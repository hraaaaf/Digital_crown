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

### Independent longitudinal implementation
Bae EJ, Kwon HJ, Kwon OW. *Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis*. Korean J Orthod. 2014;44(2):77-87. DOI: 10.4041/kjod.2014.44.2.77. PMCID: PMC3971129.

Observed study contract:
- 31 subjects with normal occlusion followed from age 9 to 19.
- 6 serial lateral cephalograms per participant at two-year intervals.
- The study uses Ricketts landmarks including PT, DC, CC, CF, XI and PM in addition to conventional hard-tissue and dental landmarks.
- It explicitly reports that age and sex must be considered for growth-sensitive Ricketts references.

This source is useful for an explicit versioned implementation and applicability review, but it does not establish one timeless universal Ricketts norm set for all populations.

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

## Source-lock decision required before code

A single profile named simply `RICKETTS_V1` is scientifically ambiguous unless its edition/composition is explicit.

The selected Digital Crown protocol must therefore:
1. declare a precise publication/edition lineage;
2. enumerate included and excluded measurements;
3. define every required landmark and construction;
4. declare norm source, population, age/sex applicability and out-of-domain behavior;
5. separate geometry availability from normative classification authority;
6. never alias generic `PT_point` to `Pt_Ricketts`;
7. never alias `Gn_anatomic` to the constructed Ricketts Gn;
8. never treat generic FMA/overjet/overbite as Ricketts measurements without a source-specific contract.

## Candidate profile strategy

Recommended target:
`RICKETTS_CLINICAL_PROFILE_1981_V1`

Status: PROVISIONAL NAME ONLY — NOT SOURCE-LOCKED.

Reason:
- 1981 provides a mature clinical lineage;
- the 2014 longitudinal study gives an independently described landmark/measurement implementation and demonstrates age/sex dependence;
- this still requires claim-by-claim definition before the profile can be frozen.

Do not call this profile “complete” until the exact composition is enumerated and every member has an executable or explicit NOT_COMPUTABLE contract.

## Required claim-by-claim matrix

For every selected measure:
`protocol measurement ID → canonical LOT06 measurement ID → source definition → landmarks → construction → unit → calibration requirement → norm set → applicability → availability behavior → UI row → tracing geometry → report section`.

Any measure without this chain remains excluded or explicitly NOT_COMPUTABLE. No fallback geometry.

## Known blockers at A0
1. `Pt_Ricketts`: explicit identity exists, but automatic legacy `PT_point` cannot be promoted by name alone.
2. `Xi`, `Pm`, `CF`, `DC`: not available as validated runtime identities in the current detector contract.
3. Ricketts mandibular plane / FH cannot inherit generic Tweed/Downs FMA semantics.
4. PTV and U6-to-PTV require an exact source-specific construction.
5. Age/sex/population-dependent normative values must not become universal classifications.
6. Active UI/report completeness for the Ricketts family is not yet demonstrated.

## A0 verdict
Ricketts is the first non-converged LOT08 protocol after Steiner and Tweed-Merrifield.

`RICKETTS_SOURCE_LOCK = NOT_SATISFIED`.

This is a productive blocker, not a code blocker to bypass. The next task is to freeze the selected profile composition and exact definitions. Only then may product code be changed.

## Next exact
1. Build the claim-by-claim Ricketts matrix from primary/independent sources.
2. Map each claim to current LOT06 registry and runtime identity support.
3. Classify each row: EXECUTABLE / MANUAL_IDENTITY_REQUIRED / NEW_CONSTRUCTION_REQUIRED / NEW_LANDMARK_REQUIRED / NORM_QUARANTINED / EXCLUDED.
4. Run two adversarial reviews:
   - A: orthodontic source fidelity / norms / applicability / fail-closed;
   - B: architecture / canonical IDs / runtime evidence / UI-report integrity / testability.
5. Freeze the profile only if both reviews find no BLOCKER/MAJOR in the proposed source contract.
6. Then start implementation.

No merge. No deployment.
