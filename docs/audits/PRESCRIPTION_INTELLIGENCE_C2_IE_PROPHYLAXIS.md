# Prescription Intelligence C2 — IE prophylaxis rule 1

Date: 2026-09-15

## Status

**CLOSED — scientific rule, structured context, read-only practitioner UI, exact-head certification, merge and post-merge regression are verified on `master`.**

## Goal

First narrow, versioned, fail-closed clinical rule for Digital Crown:

**Adult infective endocarditis prophylaxis for an eligible invasive dental procedure using oral amoxicillin.**

The rule never infers eligibility from free text. Every required input is explicit. Unknown, conflicting, pediatric, allergic, non-qualifying, wrong-medication or concurrent-penicillin cases block. Evaluation remains read-only and cannot mutate an ordonnance or silently autofill a dose.

## Scientific contract

Primary source: American Heart Association, Wilson W et al., *Prevention of Viridans Group Streptococcal Infective Endocarditis*, Circulation 2021;143:e963-e978, DOI 10.1161/CIR.0000000000000969.

Concordant source: American Dental Association, *Antibiotic Prophylaxis Prior to Dental Procedures*, rechecked 2026-09-15.

Independent cross-check: ESC 2023 infective-endocarditis guidance. C2 remains intentionally aligned to the narrower AHA/ADA dental-selection contract.

Certified READY output, only when every gate passes:

- `rule_id = IE_PROPHYLAXIS_ADULT_ORAL_AMOXICILLIN`;
- active ingredient `AMOXICILLIN`;
- adult total dose `2000 mg`;
- single dose;
- administration `30–60 minutes before` the qualifying dental procedure;
- AHA + ADA source identifiers attached;
- practitioner validation remains mandatory.

## Source-exact cardiac eligibility

Automated positive categories are restricted to:

- `PROSTHETIC_CARDIAC_VALVE`;
- `PROSTHETIC_MATERIAL_FOR_CARDIAC_VALVE_REPAIR`;
- `PREVIOUS_INFECTIVE_ENDOCARDITIS`;
- `UNREPAIRED_CYANOTIC_CONGENITAL_HEART_DISEASE`;
- `REPAIRED_CHD_WITH_RESIDUAL_SHUNT_OR_VALVULAR_REGURGITATION_AT_PROSTHETIC_PATCH_OR_DEVICE`;
- `CARDIAC_TRANSPLANT_WITH_VALVE_REGURGITATION_DUE_STRUCTURALLY_ABNORMAL_VALVE`.

`UNKNOWN`, `NONE_REPORTED` and `OTHER_CARDIAC_CONDITION` block.

The completely repaired congenital-defect scenario with prosthetic material/device during the first six months remains deliberately outside automation pending a separately reconciled current-source contract.

## Fail-closed scope

Included: adult >=18, explicit qualifying cardiac category, explicit qualifying dental procedure, explicit penicillin/amoxicillin allergy state, oral route possible, explicit current penicillin/amoxicillin exposure state, and server-side resolution of an exact single-ingredient amoxicillin CNOPS presentation.

Excluded: pediatric dosing, allergy alternatives, parenteral alternatives, post-procedure rescue dosing, unresolved six-month repaired CHD, inference from free text, automatic diagnosis interpretation, automatic antibiotic substitution, and conversion of 2 g into tablet/capsule counts.

If generic free-text medication allergy status is `PRESENT`, C2 blocks with reconciliation required rather than attempting NLP inference.

## Durable patient facts

Migration `c2ie0000002`, descending from `c1ctx0000001`, adds with `UNKNOWN` defaults:

- `penicillin_allergy_status`;
- `ie_cardiac_risk_category`.

No dose and no `clinical_ready` are persisted.

## Read-only evaluation endpoint

`POST /api/prescriptions/clinical-rules/ie-prophylaxis/evaluate`

It enforces prescription permission and tenant isolation, derives age from `date_naissance` at procedure date, reads only structured patient facts, accepts explicit prescription-scoped procedure/route/current-antibiotic facts, resolves `presentation_id` server-side, accepts only exact single-ingredient AMOXICILLINE/AMOXICILLIN, and performs no DB write, ordonnance mutation, dose autofill, `/safety/check`, or `/smart-suggest` call.

## Practitioner UI

The prescription Studio exposes a compact `Prévention endocardite` panel only for an eligible documented amoxicillin presentation. The practitioner explicitly supplies procedure date, qualifying-procedure state, oral-route state and current penicillin/amoxicillin exposure, then manually triggers `Vérifier la prophylaxie`.

The result is read-only. Internal certification jargon is not rendered to the practitioner. No posology is automatically inserted.

## UI/UX certification

BEFORE reference: Fidelity #103, artifact `10371681258`, viewports 390/430/768/1280.

AFTER exact-head: Fidelity #112, run `34920977252`, **SUCCESS**.

- artifact `10377947131`;
- digest `sha256:c55abc8567562d376e356ae350281fec8d99b237d8227445a545977c576d88c6`;
- `results.json`: PASS, failures `[]`, pageErrors `[]`;
- touch target minimum 44 px;
- no horizontal overflow;
- C2 READY rendered at all four viewports;
- no internal certification jargon visible;
- desktop preview 280 px, visible editor width 499.828 px;
- conservative human visual score: **9.0/10**.

Planning footprint vs BEFORE:

| Viewport | BEFORE | AFTER | Change |
| --- | ---: | ---: | ---: |
| 390 | 1054.875 px | 797.625 px | -24.4% |
| 430 | 975.75 px | 782.625 px | -19.8% |
| 768 | 749.75 px | 625 px | -16.6% |
| 1280 | 681.75 px | 608.75 px | -10.7% |

## Exact-head pre-merge proof

Candidate HEAD: `d4248745aeeee8def06b403dcb971b5e4b9b30b0`.

- CI #4214 / run `34920977105`: **SUCCESS**;
- full backend regression DB/patients/documents: **SUCCESS**;
- Fidelity #112: **SUCCESS**;
- PostgreSQL #629: **SUCCESS**;
- Patient P7 #1586: **SUCCESS**;
- T2 #3114: **SUCCESS**;
- Catalog #1223: **SUCCESS**;
- Settings #686: **SUCCESS**;
- M6-I #1914: SKIPPED expected.

PR #500 had no open review/comment/thread blocker and was mergeable against unchanged base `0aa34f39ca97fd3a220bc8a5d9d9d9ae3e5412c8`.

## Merge and post-merge

PR `#500 — feat(prescription): start C2 IE prophylaxis clinical rule`: **MERGED** by squash.

Merge SHA: `0097e3a08340f753803a86d2a1134880ad9ce902`, GitHub signature verified. Parent: `0aa34f39ca97fd3a220bc8a5d9d9d9ae3e5412c8`.

Post-merge CI #4216 / run `34935647891`: **SUCCESS**.

Verified jobs:

- `Tests & durcissement`: SUCCESS;
- `Full backend regression suite (DB / patients / documents included)`: SUCCESS;
- `Frontend (tests & build)`: SUCCESS;
- `Garde production (négatif)`: SUCCESS;
- M4 A/B/C contextual jobs: SKIPPED expected on push.

No Vercel deployment was requested or performed.

## Residual boundaries

C2 does not certify pediatric dosing, antibiotic alternatives, parenteral regimens, tablet-count conversion, free-text allergy interpretation, or the unresolved six-month repaired-CHD scenario. These remain fail-closed/manual by design.

## Next exact

`Select the next single clinical rule only after a new scientific contract is defined with sufficient structured context, at least two serious concordant sources, explicit fail-closed boundaries, positive/negative tests, and independent review. Do not broaden C2 implicitly.`
