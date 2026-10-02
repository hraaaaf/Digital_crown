# Cephalo 2.0 — LOT06 Must-Have Source Lock

Status: SOURCE-LOCK SUPPORT FOR CANONICAL V2 METHODS

## Scope

This document source-locks the LOT06 must-have identity/convention resolutions.
It does not activate normative interpretation, diagnosis, treatment or clinical
acceptance of analysis-pack membership.

## Primary analysis sources

- McNamara JA Jr. *A method of cephalometric evaluation*. Am J Orthod.
  1984;86(6):449-469. PMID 6594933. DOI 10.1016/S0002-9416(84)90352-X.
- Downs WB. *Variations in facial relationships; their significance in
  treatment and prognosis*. Am J Orthod. 1948;34(10):812-840.
  PMID 18882558. DOI 10.1016/0002-9416(48)90015-3.
- Merrifield LL. *The profile line as an aid in critically evaluating facial
  esthetics*. Am J Orthod. 1966;52(11):804-822. PMID 5223046.
  DOI 10.1016/0002-9416(66)90250-8.
## Canonical landmark identity boundary

Digital Crown preserves legacy persisted IDs. Canonical scientific consumers use
explicit additive identities only when provenance is certified:

- Po_anatomic: anatomical porion; never machine/ear-rod porion.
- Co_anatomic: anatomical condylion; never a generic condylar center.
- Gn_anatomic: anatomical gnathion; never a constructed Gn.
- Pog_hard: hard-tissue pogonion; never soft-tissue Pog'.

Supporting landmark literature describes anatomical porion at the superior/upper
external auditory meatus, condylion at the superior/posterosuperior condylar
point, gnathion on the bony chin/symphysis, and pogonion as the anterior bony
chin point. The executable identity remains governed by the Digital Crown
SRPose38 contract and LOT03 atlas, not by name similarity alone.

Supporting literature:
- PMCID PMC12313948 — benchmark landmark definitions including Co, Gn, Po.
- PMCID PMC8703373 — Po, Co and Gn definitions.
- PMCID PMC13466904 — Po and Pog definitions.
## Convention split

The historical generic canonical ID
`M_FACIAL_ANGLE_NPOG_FH_DEG_V1` is superseded for execution because it hid a
convention collision.

LOT06 therefore keeps two independent canonical measurements:

- `M_DOWNS_FACIAL_ANGLE_NPOG_FH_ACUTE_DEG_V1`
- `M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1`

They are separate scientific identities even though both depend on the
Frankfort and N-Pog geometry. No value substitution or convergence rule is
allowed between them.

## Fail-closed residual

Ricketts facial axis remains non-promoted until an exact
`Pt_Ricketts` landmark identity is available. Generic legacy `PT_point` is
not accepted as an implicit substitute.

## Compatibility

Legacy V1 measurement methods remain readable and retain their historical
semantics. Canonical V2/V3 methods are additive and use explicit identities.
No persisted legacy landmark is renamed or migrated in place.
