# V1-05 Ortho Journey — F3 Closeout

Status: **HUMAN VISUAL VALIDATED — FINAL CERTIFICATION IN PROGRESS**

## Trailer

F3 lets the practitioner compare two orthodontic timepoints such as T0 and T1 directly from the patient Overview.

It shows:
- selected timepoints and dates
- canonical evidence inventory on both sides
- common certified cephalometric measurements
- signed arithmetic deltas only

It never generates a clinical verdict about improvement, worsening, success, failure or treatment effect.

## Product baseline

Parent F2 merge:
`35ccdf5ad73b403279e129c7affe2d9364c6d4cc`

Product PR:
#613

## BEFORE

Exact merged F2 baseline.

Workflow:
`Ortho F3 BEFORE`

Certified successful run:
`35398665459`

Viewports:
- 390×844
- 768×1024
- 1280×900

BEFORE contract:
- generic Patient Journey visible
- no F3 compare surface
- no T0/T1 comparison UI
- no horizontal overflow

## Goal + mockup

- `docs/clinic/audits/V1_05_F3_LONGITUDINAL_COMPARE_GOAL.md`
- `docs/clinic/audits/V1_05_F3_LONGITUDINAL_COMPARE_MOCKUP.md`

## Implemented backend

- read-only compare endpoint
- no new persistence
- exact scoped patient/case/timepoint selection
- canonical evidence inventory
- common cephalometric measurement extraction
- arithmetic delta only
- linear mm values require both cephalometric analyses calibrated
- multiple cephalos on either side => neutral ambiguity state; no guessing

## Implemented frontend

Patient Details → Vue d’ensemble:
- dedicated “Comparaison orthodontique” panel before generic Patient Journey
- T0/T1 selectors
- swap action
- evidence lanes
- desktop/tablet measurement table
- mobile stacked measurement cards
- explicit caption: “Variation numérique — interprétation clinique par le praticien.”

## Clinical boundary

Forbidden:
- automatic improvement / worsening label
- treatment success / failure
- progress scoring
- normative threshold interpretation
- recommendation
- superimposition

F5 remains separate.

## Visual score rubric — severe

Score is assigned only after AFTER evidence is green.

Dimensions:
1. hierarchy / findability — 2.0
2. T0/T1 comparison clarity — 2.0
3. evidence provenance readability — 1.5
4. mobile/tablet/desktop responsiveness — 2.0
5. visual consistency with PatientDetails — 1.5
6. clinical-neutrality communication — 1.0

Maximum: 10.0

No 10/10 without direct visual proof on all three certified viewports.

## Certification pending

Current candidate HEAD:
`6bb46299ce556a49c1efe8f546016a55d1912e6b`

Pending:
- Ortho F3 AFTER
- CI
- P7
- T2
- A5
- Full Backend product-equivalent proof after exact-head gates are green

## Next

If AFTER is green:
1. inspect artifact/report
2. compare BEFORE vs AFTER on identical viewports
3. assign severe visual score
4. fix if score or evidence is insufficient
5. exact-head + Full Backend certification
6. human merge gate
7. merge + post-merge proof
8. F4 cockpit practitioner


## Final human visual validation

Human gate:
- desktop/tablet accepted in the first AFTER review
- mobile initially rejected as too vertically dense
- mobile-only polish applied at `152d39f34e76d00162f80d58da21389e843d39b2`
- polished mobile AFTER re-captured and explicitly validated by the product owner

Polished exact-head visual proof:
- Ortho F3 AFTER `35402797193` — SUCCESS
- BEFORE `35402797259` — SUCCESS
- CI `35402797295` — SUCCESS
- T2 `35402797297` — SUCCESS
- A5 `35402797197` — SUCCESS
- Cephalo R15 `35402797310` — SUCCESS
- Cephalo R15bis `35402797280` — SUCCESS
- Media C4 `35402797276` — SUCCESS
- Patient UX1-C `35402797360` — SUCCESS

AFTER artifact:
- id `10570369062`
- digest `sha256:d8c00bc20ea5e1c04582c27e78d8d1cc5c1a2a416a4701ef7b23274116125d36`

Certified viewports:
- 390×844
- 768×1024
- 1280×900

Visual score — severe:
- hierarchy / findability: 1.9 / 2.0
- T0/T1 comparison clarity: 1.9 / 2.0
- evidence provenance readability: 1.4 / 1.5
- responsiveness: 1.9 / 2.0
- PatientDetails visual consistency: 1.4 / 1.5
- clinical-neutrality communication: 1.0 / 1.0

**Total: 9.5 / 10**

Reason score is not 10/10:
- evidence rows remain intentionally compact rather than visually rich
- F3 is a focused comparator, not the full practitioner cockpit; broader synthesis belongs to F4

## Final certification

Temporary Full Backend PR:
- #615
- product-equivalent base `152d39f34e76d00162f80d58da21389e843d39b2`
- cert-only commit `6e7464e46628106d4c23b37be3eb7afc078407f8`
- delta: `.github/workflows/ci.yml` only
- MUST NOT MERGE
