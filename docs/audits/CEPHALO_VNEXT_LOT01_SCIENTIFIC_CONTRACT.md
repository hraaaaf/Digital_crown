# Cephalo vNext — LOT01 Scientific Contract

Status: CANDIDATE — documentation only, no runtime change
Baseline: master 71efbb62db60fbb2152c7f70e263b500a44f2c80
Gate target: CEPH_SCIENTIFIC_CONTRACT_APPROVED

## Goal / Success / Proof

**Goal** — lock the scientific identity of every landmark and analysis before detector/schema/runtime work.

**Success** — no detector output, similarly named point, construction, norm or analysis variant is promoted by name alone. Every clinically consumed item has an explicit version, provenance and fail-closed state.

**Proof** — existing Digital Crown source locks and geometry fixtures, primary analysis sources already recorded in the repository, plus external benchmark evidence used only for validation/generalization.

## Non-negotiable contracts

1. Landmark != construction != plane/line != measurement != normative profile != interpretation.
2. Detector availability never proves anatomical identity.
3. A shared mathematical primitive may be reused only while analysis-specific semantics remain explicit.
4. Missing/ambiguous inputs return NOT_COMPUTABLE / BLOCKED rather than a nearby substitute.
5. Historical norms remain inactive unless population, age/sex model, modality, scaling and analysis version are source-locked.
6. Lateral cephalometry cannot silently produce PA/frontal factors.
7. Human correction and provenance remain part of the clinical chain.
8. Existing patient studies/reports must remain readable across future schema/model migrations.

## Canonical analysis versions

| Family | Canonical contract | Decision |
|---|---|---|
| Steiner | STEINER_1953_CORE_V1 | core |
| Steiner extension | STEINER_1959_CLINICAL_EXTENSION_V1 | separate version |
| Downs | DOWNS_1948_CORE_V1 | primary source locked; geometry only until per-measure implementation proof |
| Wits / Jacobson | WITS_JACOBSON_1975_V1 | standalone sagittal appraisal; never relabelled Steiner/Downs |
| Tweed | DC_TWEED_ANATOMICAL_FH_VARIANT | selected DC Po-Or contract; not strict 1954 ear-rod geometry |
| Merrifield | separate analysis/version | never merged into Tweed silently |
| McNamara | MCNAMARA_1984_SINGLE_FILM_V1 | lateral core |
| Ricketts | RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1 | 11 lateral + 12 frontal; frontal fail-closed without PA |
| CRANIOM/COM | COM_DC_LEGACY_V1 / CRANIOM provenance per metric | composite compatibility layer, never falsely attributed |

## Landmark identity gates

| Scientific target | SRPose38 channel | Aariz 29 | Contract |
|---|---|---|---|
| S,N,A,B,Or,Po,Pog,Me,Gn,Go,ANS,PNS,Ar,Co | present | present | anatomy must be independently validated; SRPose mapping remains LEGACY_AUTO_UNVERIFIED |
| U1 apex/incisal, L1 apex/incisal | present | present | usable only after channel/anatomy validation |
| Prn/Pn, Sn, Ls, Li, soft Pog | present | present | soft-tissue correspondence must be alias-locked |
| D_Steiner_1959 | D_point exists | absent | SOURCE_LOCK_REQUIRED; no automatic equivalence |
| Pt_Ricketts | PT_point exists | absent | source definition + channel validation required |
| PTM_McNamara | Ptm exists | absent | distinct from Pt_Ricketts |
| Ba | present | absent | channel validation required |
| Gn_anatomic | Gn exists | present | distinct from constructed Gn |
| Gn_constructed | constructed | n/a | explicit construction, never detector alias |
| Xi_Ricketts / Pm_Ricketts | absent | absent | BLOCKED_LANDMARK |
| U1/L1 facial crown surface | absent | absent | BLOCKED_LANDMARK for strict linear Steiner/McNamara measures |
| U6/L6 source-specific crown point | generic U6/L6 | Aariz molar cusp tips | BLOCKED until each analysis point is source-locked; generic/cusp/distal are not interchangeable |
| airway landmarks | absent | absent | BLOCKED_LANDMARK |
| PA/frontal landmarks | absent lateral contract | absent | BLOCKED_MODALITY_PA |

## Aariz/CEPHA29 role

Aariz is a **validation/generalization benchmark**, not the canonical Digital Crown schema.

External facts to preserve:
- 1000 lateral cephalograms;
- 29 landmarks: 15 skeletal, 8 dental, 6 soft-tissue;
- seven imaging devices;
- expert annotation/review by six orthodontists;
- train/validation/test partition and per-device diversity;
- public dataset on Figshare under CC BY 4.0.

Aariz overlaps strongly with the classical DC core but does not cover all SRPose38 extension points. Its value is therefore cross-device external validation and clinically reviewed landmark correspondence, not replacing the 38-channel contract.

## Measurement / norm gates inherited from baseline

Promote only measurements whose exact landmark + construction + analysis version is locked.

Known fail-closed examples:
- Steiner U1-NA mm / L1-NB mm: facial crown surface missing.
- Steiner SND: D identity not yet proven.
- Ricketts Oral Gnomon: Xi/Pm missing.
- Ricketts strict mandibular plane: Sub.Go.-M contract missing.
- Ricketts U6-PTV: distal crown + strict PTV contract missing.
- McNamara airway: dedicated landmarks missing.
- Ricketts frontal 12 factors: PA modality missing.
- legacy norms in normative_profiles.yaml remain LEGACY_UNVALIDATED where marked; conflicting values must not be silently reconciled.

## Acceptance criteria for future detector/schema work

A landmark can become AUTO_VALIDATED only when all are proven:
1. anatomical definition source-locked;
2. detector channel correspondence demonstrated;
3. calibration/scaling path verified;
4. accuracy reported per landmark in mm, not only global MRE;
5. clinically relevant downstream angular/linear error assessed where applicable;
6. cross-device validation performed;
7. confidence/failure behavior defined;
8. manual correction + provenance preserved;
9. migration compatibility tested;
10. no downstream analysis is activated unless its own source contract is satisfied.

## Gate decision

LOT01 may reach CEPH_SCIENTIFIC_CONTRACT_APPROVED only after adversarial review confirms:
- no hidden equivalence between Pt/PTM, anatomical/constructed Gn, hard/soft Pog, generic/source-specific molars, or Tweed/Ricketts mandibular/Frankfort variants;
- all legacy norms remain explicitly versioned and non-authoritative unless proven;
- Aariz is used as benchmark evidence rather than silently redefining the Digital Crown landmark ontology.

No runtime, DB, patient, report, detector or UI mutation is authorized by this document.

## Debt-zero source-lock addendum

### Downs 1948
Primary source lock: W. B. Downs, *Variations in facial relationships; their significance in treatment and prognosis*, American Journal of Orthodontics 34(10):812–840 (1948), DOI 10.1016/0002-9416(48)90015-3, PMID 18882558.

Canonical family: `DOWNS_1948_CORE_V1`. The retained geometry family includes facial angle, angle of convexity, A-B plane angle, mandibular-plane/FH relation, Y-axis/FH, occlusal-plane/FH, interincisal relation and incisor/plane relations only when their exact required constructions are available. Normative interpretation is not activated by this source lock alone. Missing exact occlusal or dental construction remains NOT_COMPUTABLE; no substitute plane or crown point is allowed.

### Wits / Jacobson 1975
Primary source lock: A. Jacobson, *The “Wits” appraisal of jaw disharmony*, American Journal of Orthodontics 67(2):125–138 (1975), DOI 10.1016/0002-9416(75)90065-2, PMID 1054214.

Canonical contract: `WITS_JACOBSON_1975_V1`. A and B are projected perpendicularly to the occlusal plane to produce AO and BO; the sagittal AO–BO relation is the measurement. It is a distinct analysis and MUST NOT be inferred from ANB or renamed as a Steiner measurement. If the required occlusal-plane construction is unavailable or ambiguous, Wits is NOT_COMPUTABLE.

### Decision
Downs and Wits/Jacobson are no longer undocumented analysis families. Their primary bibliographic identities and non-substitution rules are source-locked. Quantitative population norms remain separate normative evidence and are not silently activated.
