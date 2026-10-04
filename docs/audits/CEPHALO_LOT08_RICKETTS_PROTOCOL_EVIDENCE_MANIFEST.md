# LOT08 — Ricketts Protocol Evidence Manifest — A0

Date: 2026-10-04  
Branch: `feat/ortho-studio-lot08-ricketts-protocol`  
Base: `master@19a91889b8b60ea97e49f717909be9cc83fdf919`

## Goal
Converge the Ricketts family as a **complete, versioned protocol library**, consistent with the already-fixed Cephalo 2.0 product doctrine: no timeless single "Ricketts", no silent variant merging, no reduction to a minimal historical subset.

## Canonical product decision recovered
The existing LOT08 canonical roadmap already fixes the architecture:
- every analysis is a versioned `protocol_profile`;
- each profile includes structures, constructions, measurements, norm sets, protocol-derived interpretations and report sections;
- no pack may be called complete unless composition is source-locked and explicitly versioned;
- historical/editorial variants must be declared rather than silently merged;
- custom analysis may select/reorder verified LOT06 measurements but cannot create a parallel scientific authority.

Therefore, **the new Digital Crown Ricketts is not the 1960 five-measure system alone**. The 1960 paper is historical/source context and may become a separate profile, but LOT08 product parity requires explicit modern/comprehensive and simplified Ricketts variants where source-lock can be established.

## Market benchmark — verified vendor behavior

### Dolphin Imaging
Official Dolphin material states:
- >400 lateral analyses including Ricketts;
- fully customizable analyses, structures and norms;
- norms can be categorized by gender, age and race;
- dedicated **5-part Ricketts superimposition**;
- longitudinal measurement tables and progress superimposition.

Product lesson: Ricketts is treated as a rich analysis/superimposition family, not a five-row static table.

### Facad
Official Facad material states:
- standard + local/custom analyses;
- analyses may be modified through an analysis editor;
- current standard library includes:
  - **32 factor Ricketts analysis**;
  - **Simplified 13 factor Ricketts analysis**;
  - a separate Ricketts adaptation attributed to Gerry Samson;
- Facad also has a distinct frontal Ricketts analysis.

Product lesson: explicit **comprehensive vs simplified Ricketts variants** is normal market behavior.

### AudaxCeph
Official AudaxCeph material states:
- 200+ analysis types;
- Ricketts is included in the downloadable analysis library;
- analysis types can be fine-tuned;
- users can create analysis types from points, planes, measurements, calculated measurements, standard values and reports;
- superimposition, growth projection, VTO/STO are first-class downstream workflows.

Product lesson: Ricketts is a configurable protocol package inside a larger clinical workflow.

### WebCeph
Official WebCeph documentation/manual states:
- Ricketts is one of the built-in analysis methods alongside Steiner, Tweed, McNamara, Downs, Jarabak, Eastman and Wits;
- Analysis Wizard + Measurement Wizard support custom methods;
- WebCeph added custom CC and CF point support for Ricketts;
- Ricketts superimposition exists as a Premium feature;
- importantly, WebCeph support explicitly declined to define one universal "Full Ricketts" because average values vary across races/references and instead directs users to custom analysis/measurement tools.

Product lesson: variant/norm ambiguity is real and must be encoded rather than hidden.

## External scientific baseline

Primary lineage:
1. Ricketts RM. *A foundation for cephalometric communication*. Am J Orthod. 1960;46:330-357. DOI: 10.1016/0002-9416(60)90047-6.
2. Ricketts RM. *Perspectives in the clinical application of cephalometrics. The first fifty years*. Angle Orthod. 1981;51(2):115-150. DOI: 10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2.

Independent longitudinal implementation:
Bae EJ, Kwon HJ, Kwon OW. *Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis*. Korean J Orthod. 2014;44(2):77-87. DOI: 10.4041/kjod.2014.44.2.77. PMCID: PMC3971129.

The 2014 study uses extended Ricketts landmarks including PT, DC, CC, CF, XI and PM and demonstrates age/sex dependence for several measurements. It is an independent population-specific reference, not a universal norm authority.

## Repo baseline on current master

Existing source-aware/canonical-v2 capability includes:
- facial depth;
- maxillary convexity;
- E-line Ls/Li;
- facial axis with explicit `Pt_Ricketts` and constructed Ricketts Gn;
- explicit fail-closed behavior when `Pt_Ricketts` is unavailable;
- source-specific distinction between Ricketts facial depth and Downs facial angle.

Still unresolved/non-promoted according to current completeness audit:
- Ricketts-specific mandibular plane/FH;
- lower facial height;
- maxillary depth;
- mandibular arc;
- corpus length;
- lower incisor to A-Pog distance and inclination;
- source-specific overjet/overbite;
- U6 to PTV;
- internal structures requiring Xi/Pm/CF/DC and related constructions.

Therefore LOT06 coverage is useful infrastructure, not proof of LOT08 Ricketts completeness.

## Corrected protocol-family strategy

### Profile A — comprehensive Ricketts
Provisional product ID:
`RICKETTS_COMPREHENSIVE_32_PROTOCOL_V1`

Intent:
match the market expectation represented explicitly by Facad's 32-factor Ricketts offering, **only after the exact 32-factor composition and definitions are source-locked**.

Status:
PRODUCT TARGET IDENTIFIED / COMPOSITION NOT YET SOURCE-LOCKED.

Important:
"32" is currently a vendor-observed product variant, not yet a Digital Crown scientific definition. Do not implement or name individual members from memory.

### Profile B — simplified Ricketts
Provisional product ID:
`RICKETTS_SIMPLIFIED_13_PROTOCOL_V1`

Intent:
provide a clinically practical reduced profile comparable to Facad's simplified 13-factor variant, again only after exact composition/source lock.

Status:
PRODUCT TARGET IDENTIFIED / COMPOSITION NOT YET SOURCE-LOCKED.

### Profile C — historical communication
Optional historical/source profile:
`RICKETTS_COMMUNICATION_1960_PROTOCOL_V1`

Intent:
preserve the original five-measure communication system as a historically explicit profile if useful.

Status:
SECONDARY / NOT THE MAIN "NEW RICKETTS" PRODUCT TARGET.

### Profile D — frontal / PA Ricketts
Separate future profile:
`RICKETTS_FRONTAL_PROTOCOL_V1`

Reason:
Dolphin and Facad both expose frontal Ricketts independently from lateral analysis. No lateral↔PA conflation.

## Normative architecture
No Ricketts profile inherits one universal norm table.

Every norm set must encode:
- source/version;
- population;
- age range or age model;
- sex where applicable;
- unit/method;
- applicability;
- fail-closed/out-of-domain behavior.

If applicability is unsupported:
- show the measurement;
- show provenance/reference where allowed;
- suppress protocol-derived classification.

## Required claim-by-claim contract

For every member of each retained profile:
`profile → measurement ID → LOT06 canonical ID → exact source definition → landmarks → construction → unit → calibration → norm set → applicability → fail-closed state → UI row → tracing geometry → report section`.

No fallback geometry. No generic FMA/overjet/overbite relabelled as Ricketts without a source-specific contract.

## Known blockers
1. Exact composition/source authority of the **32-factor** profile is not yet locked.
2. Exact composition/source authority of the **13-factor** profile is not yet locked.
3. `Pt_Ricketts` cannot be silently aliased from generic `PT_point`.
4. `Xi`, `Pm`, `CF`, `DC` are not yet validated runtime identities.
5. PTV and U6→PTV need source-specific construction.
6. Ricketts-specific mandibular plane/FH cannot inherit Tweed/Downs semantics.
7. Population/age/sex norms require explicit applicability.
8. UI/report completeness is not yet demonstrated.
9. LOT06 provisional `RICKETTS_V1` pack must map explicitly into final LOT08 profiles.

## Adversarial review A — source/product fidelity
Finding on previous A0: MAJOR.
The previous draft over-corrected toward the 1960 five-measure system and would have produced a product materially below the already-fixed Digital Crown roadmap and current market references.

Correction:
- restore "complete A→Z, versioned variants" as the product goal;
- target comprehensive + simplified Ricketts profiles;
- keep 1960 communication as optional historical profile;
- keep frontal Ricketts separate;
- preserve norm applicability guards.

Post-correction severe score: 9.5/10.

## Adversarial review B — architecture/authority
Finding on previous A0: MAJOR.
Equating source purity with a single historical profile would have made LOT08 scientifically neat but product-incomplete. Conversely, copying vendor "32/13 factor" labels without source-lock would create a new unverified authority.

Correction:
- vendor variants define product parity targets only;
- exact compositions remain blocked until independent scientific/source extraction;
- all executable measurements still flow through LOT06 canonical IDs;
- custom composition never writes formulas.

Post-correction severe score: 9.5/10.

## Confirmation
Rechecked against:
- canonical LOT08 roadmap;
- recovered LOT08 A0;
- current master completeness audit;
- official Dolphin, Facad, AudaxCeph and WebCeph product material.

Result:
0 new BLOCKER / 0 new MAJOR in the **corrected product framing**.
Scientific source-lock remains OPEN by design.

## A0 verdict
Ricketts remains the first non-converged LOT08 protocol family.

`RICKETTS_SOURCE_LOCK = NOT_SATISFIED`.

Correct target:
**comprehensive + simplified + optional historical + separate frontal**, all versioned.

## Next exact
1. Obtain/source-lock the exact composition of the comprehensive and simplified Ricketts variants.
2. Build the 32-row and 13-row matrices without inventing membership.
3. Map every retained row to LOT06 IDs and runtime landmark/construction support.
4. Mark unsupported rows fail-closed rather than dropping them silently.
5. Run source/orthodontic and architecture/QA reviews from zero.
6. Only then implement Ricketts UI/report/tracing.

No merge. No deployment.


## A1 supersession — 2026-10-04

The A0 product labels `RICKETTS_COMPREHENSIVE_32_PROTOCOL_V1` and `RICKETTS_SIMPLIFIED_13_PROTOCOL_V1` are superseded as **scientific profile IDs** by the source-lock pass in:
`docs/audits/CEPHALO_LOT08_RICKETTS_32_13_SOURCE_LOCK_MATRIX.md`.

Reason:
- official Facad material proves the vendor labels 32 F / 13 F and cites the 2009 Atlas;
- the publicly indexed 2009 Atlas chapter itself describes **33 factors** in the complete analysis and a **12-factor** summary;
- a separate Gregoret 1997 lineage supports a distinct **13-factor** summarized profile.

Canonical source-qualified targets are therefore:
- `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1` — main complete profile;
- `RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1` — main practical summary;
- `RICKETTS_ATLAS_2009_SUMMARY_12_PROTOCOL_V1` — optional distinct summary;
- Facad 32F/13F remain compatibility targets until their exact row membership is independently observed.

This delta does not authorize code. `RICKETTS_SOURCE_LOCK` remains OPEN.
