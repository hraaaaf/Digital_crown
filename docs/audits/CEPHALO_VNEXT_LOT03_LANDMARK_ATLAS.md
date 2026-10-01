# Cephalo vNext — LOT03 Landmark Atlas

Status: CANDIDATE — documentation only
Parent: LOT02 candidate ed955dce3a289bac995d83e2680577b91fcbc2f3
Gate target: CEPH_LANDMARK_SET_APPROVED

## Goal
Map the three distinct contracts without inventing equivalence:
1. Aariz/CEPHA29 anatomical labels;
2. SRPose38 output channels;
3. Digital Crown canonical/consumer IDs.

## Important count correction
SRPose38 emits exactly 38 model channels. The current frontend `REQUIRED_LANDMARKS` contract contains **40 IDs**, because it also requires `Occ_Ant` and `Occ_Post`, which are not SRPose38 output channels. Therefore "frontend 38" is false; the correct baseline is **38 detector outputs + 2 additional occlusal-plane IDs = 40 frontend-required IDs**.

## Aariz29 ↔ SRPose38 ↔ Digital Crown

| Aariz | Aariz definition/title | SRPose38/DC candidate | Status |
|---|---|---|---|
| A | A-point | A | DIRECT_NAME_MATCH — anatomy validation still required |
| ANS | Anterior Nasal Spine | ANS | DIRECT_NAME_MATCH |
| B | B-point | B | DIRECT_NAME_MATCH |
| Me | Menton | Me | DIRECT_NAME_MATCH |
| N | Nasion | N | DIRECT_NAME_MATCH |
| Or | Orbitale | Or | DIRECT_NAME_MATCH |
| Pog | Pogonion | Pog | DIRECT_NAME_MATCH hard tissue |
| PNS | Posterior Nasal Spine | PNS | DIRECT_NAME_MATCH |
| Pn | Pronasale | Prn | ALIAS_CANDIDATE; definition/source lock required |
| R | Ramus | none | AARIZ_ONLY — definition and clinical utility to assess |
| S | Sella | S | DIRECT_NAME_MATCH |
| Ar | Articulare | Ar | DIRECT_NAME_MATCH |
| Co | Condylion | Co | DIRECT_NAME_MATCH |
| Gn | Gnathion | Gn | DIRECT_NAME_MATCH anatomical; never constructed Gn |
| Go | Gonion | Go | NAME_MATCH_DEFINITION_HOLD; anatomical vs constructed convention matters |
| Po | Porion | Po | NAME_MATCH_CAUTION; anatomical vs ear-rod variants |
| LPM | Lower 2nd PM Cusp Tip | none | AARIZ_ONLY — useful candidate for occlusal-plane/tracing contract |
| LIT | Lower Incisor Tip | L1_incisal | ALIAS_CANDIDATE |
| LMT | Lower Molar Cusp Tip | L6 | SEMANTIC_HOLD — generic SRPose/DC "Lower Molar" does not prove cusp-tip identity |
| UPM | Upper 2nd PM Cusp Tip | none | AARIZ_ONLY — useful candidate for occlusal-plane/tracing contract |
| UIA | Upper Incisor Apex | U1_apex | ALIAS_CANDIDATE |
| UIT | Upper Incisor Tip | U1_incisal | ALIAS_CANDIDATE |
| UMT | Upper Molar Cusp Tip | U6 | SEMANTIC_HOLD — generic "Upper Molar" does not prove cusp-tip identity |
| LIA | Lower Incisor Apex | L1_apex | ALIAS_CANDIDATE |
| Li | Labrale inferius | Li_soft | ALIAS_CANDIDATE |
| Ls | Labrale superius | Ls_soft | ALIAS_CANDIDATE |
| N` | Soft Tissue Nasion | N_soft | ALIAS_CANDIDATE |
| Pog` | Soft Tissue Pogonion | Pog_soft | ALIAS_CANDIDATE; never hard Pog |
| Sn | Subnasale | Sn_soft | ALIAS_CANDIDATE |

## SRPose38 points not covered by Aariz29
Aariz does not annotate these SRPose38 channels: `D_point`, `Cm`, `Ptm`, `Ba`, `PT_point`, `Bo`, `Ls2`, `Li2`, `Gn_soft`, `Me_soft`, `G_soft`, `C_point`.

They remain Digital Crown candidates only if source identity + downstream utility + detector validation are proven. Aariz cannot validate them.

## Aariz-only additions worth investigating
Aariz contains three labels with no direct SRPose38 channel:
- `R` — Ramus: do not add until its precise anatomical definition and useful analysis/tracing dependency are demonstrated.
- `UPM` — Upper 2nd premolar cusp tip.
- `LPM` — Lower 2nd premolar cusp tip.

UPM/LPM are high-value candidates because a source-locked premolar/molar dental pair may support a reproducible occlusal-plane construction and richer anatomical tracing. This is a hypothesis to validate, not yet an approved runtime addition.

## Constructed/non-detector IDs
`Occ_Ant` and `Occ_Post` are frontend-required but are not SRPose38 outputs and are not Aariz labels. Their provenance/construction must be source-locked separately; they must never be counted as detector landmarks.

Likewise, `Gn_constructed`, N-perpendicular, PTV, A-vertical and other constructions remain derived entities, not detector labels.

## Proposed Cephalo 2.0 landmark policy
The target is not "Aariz29 replaces SRPose38" and not "all 38 are automatically clinical".

Three layers:
- **L1 CLINICAL_CANONICAL** — source-locked anatomy required by approved measurements.
- **L2 TRACING_CANONICAL** — source-locked points useful primarily for anatomical tracing/planes.
- **L3 RESEARCH_CANDIDATE** — detector/dataset points retained for benchmark or future analyses but not consumed clinically.

Aariz labels may enter L1/L2 only after definition compatibility is proven. SRPose38-only labels follow the same rule.

## Source-lock findings

Aariz's published data descriptor resolves the three previously vague Aariz-only labels:
- `R` = most convex point on the exterior border of the ramus along the vertical.
- `UPM` = buccal cusp tip of the upper second premolar.
- `LPM` = buccal cusp tip of the lower second premolar.
- `UMT`/`LMT` = mesiobuccal cusp tip of the upper/lower first molar.
- Aariz `Po` is explicitly **anatomic porion**, at the upper contour of the external auditory canal.
- Aariz `Go` is the midpoint of the contour connecting ramus and mandibular body; this is not proof of equivalence to every constructed/source-specific Gonion.
- Aariz `Gn` is a midpoint-type anatomical chin definition and must not be substituted for a source-specific constructed Gn.

Therefore:
- `UMT/LMT ↔ SRPose U6/L6` stays **SEMANTIC_HOLD** until the SRPose/CL-Detection molar channel is proven to be the mesiobuccal cusp tip.
- `Po_Aariz ↔ Po_anatomic` is anatomically compatible in definition, but detector validation is still required. Machine/ear-rod Porion remains a distinct entity; published work demonstrates measurable PoA/PoM differences.
- `Go_Aariz ↔ Go` remains analysis-sensitive because published cephalometric conventions include contour and constructed/intersection variants.
- `R` is useful for tracing/ramus morphology but no approved LOT01 clinical measurement currently requires it; initial disposition = L2_TRACING_CANDIDATE.
- `UPM/LPM` are source-locked cusp landmarks and useful candidates for an occlusal-plane construction, but the **analysis-specific occlusal plane itself remains SOURCE_LOCK_REQUIRED**. The existence of premolar contacts/cusps does not authorize one universal occlusal-plane definition.

### Initial L1/L2/L3 disposition

**L1 clinical candidates:** S,N,Or,Po_anatomic,A,B,Pog_hard,Me,ANS,PNS,Ar,Co,U1/L1 incisal tips and apices, Prn,Sn,Ls,Li,Pog_soft — subject to per-channel validation and analysis-specific gates.

**L1 versioned identities, never generic aliases:** `Gn_Aariz_midpoint`, `Gn_constructed_<analysis>`, `Go_Aariz_contour_midpoint`, `Go_constructed_<analysis>`, `Po_anatomic`, and any `Po_machine/ear_rod` variant. The current runtime IDs `Gn`, `Go`, `Po` are compatibility aliases only until a consumer binds an explicit scientific identity.

**L2 tracing/construction candidates:** R, UPM, LPM, Cm, Ba, Ptm, G_soft, N_soft, Gn_soft, Me_soft, C_point where their definitions/provenance are locked.

**L3 research/source-specific hold:** D_point, PT_point, Bo, Ls2, Li2, generic U6/L6 until exact semantics are proven. A point may move from L3 only through a versioned evidence decision.

## Decisions requiring evidence before gate
1. Confirm Aariz Pn ↔ DC Prn against the DC operational definition before alias promotion.
2. Prove/deny Aariz LMT/UMT ↔ SRPose38 L6/U6; do not infer cusp tip from "molar".
3. R/UPM/LPM definitions are now source-locked from Aariz; preserve R as L2 candidate and keep UPM/LPM conditional on an analysis-specific occlusal-plane contract.
4. Bind every Go consumer to an explicit versioned Go identity; no generic Go promotion.
5. Bind every Po/FH consumer to `Po_anatomic` or an explicit machine/ear-rod variant; no generic Po promotion.
5a. Bind every Gn consumer to an explicit anatomical or constructed definition; no generic Gn promotion.
6. Define occlusal plane points/construction; assess whether UPM/LPM improve it.
7. Classify all SRPose38-only channels L1/L2/L3 with explicit downstream utility.
8. Keep D/Pt/PTM and anatomical/constructed Gn identities separate.
9. Keep hard/soft tissue aliases separate.
10. Do not approve any point based solely on model availability.

## Gate
`CEPH_LANDMARK_SET_APPROVED` requires exact definitions and evidence for all L1/L2 points, explicit L3 disposition, and reviewed mapping to the LOT01/LOT02 contracts.

No runtime/schema/model/master mutation is authorized.
