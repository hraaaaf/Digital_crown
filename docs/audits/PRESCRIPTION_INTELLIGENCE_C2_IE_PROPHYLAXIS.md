# Prescription Intelligence C2 — IE prophylaxis rule 1

Date: 2026-09-15

## Status

ACTIVE — scientific/backend rule + structured patient facts + read-only evaluation endpoint implemented on an isolated branch. No UI suggestion and no automatic prescription activation.

## Goal

Implement the first narrow, versioned, fail-closed clinical rule for Digital Crown:

**Adult infective endocarditis prophylaxis for an eligible invasive dental procedure using oral amoxicillin.**

Success means:

- the rule never infers eligibility from free text;
- every required input is explicit;
- unknown, conflicting, pediatric, allergic, non-qualifying, wrong-medication or concurrent-penicillin cases block;
- only the fully eligible adult path returns the source-backed regimen;
- the result is traceable to a rule id, rule version and source ids;
- evaluation is read-only and cannot mutate an ordonnance or silently autofill a dose;
- no practitioner-facing activation occurs before independent scientific review and UI certification.

## Scientific sources

### Primary source 1 — American Heart Association

Wilson W et al. *Prevention of Viridans Group Streptococcal Infective Endocarditis: A Scientific Statement From the American Heart Association.* Circulation. 2021;143:e963-e978. DOI: 10.1161/CIR.0000000000000969.

Relevant source-backed rule elements:

- prophylaxis is limited to patients at highest risk of adverse outcome from VGS infective endocarditis;
- qualifying dental procedures include manipulation of gingival tissue, manipulation of the periapical region, or perforation of oral mucosa;
- oral amoxicillin adult regimen: **2 g single dose 30 to 60 minutes before the procedure**;
- pediatric regimen is weight-based and is intentionally outside this C2 rule;
- clindamycin is no longer recommended as a prophylaxis alternative in the AHA 2021 statement.

### Concordant source 2 — American Dental Association

ADA. *Antibiotic Prophylaxis Prior to Dental Procedures.* Current ADA oral-health topic page, accessed 2026-09-15.

Relevant source-backed rule elements:

- follows the AHA infective-endocarditis prophylaxis recommendations;
- prophylaxis is restricted to a small high-risk cardiac subset undergoing qualifying dental procedures;
- if a patient requiring prophylaxis is already taking amoxicillin/penicillin-class therapy, AHA/ADA recommend selecting an antibiotic from a different class rather than silently repeating amoxicillin.

### Cross-check — ESC

ESC 2023 infective-endocarditis guidance was reviewed as an independent cross-check. C2 remains intentionally aligned to the AHA/ADA dental selection contract rather than merging societies into a broader eligibility rule.

## Independent cardiac-taxonomy review

The first broad enum `QUALIFYING_CONGENITAL_HEART_DISEASE` was rejected before activation because it could incorrectly imply that all congenital heart disease qualifies.

The current fail-closed positive categories are source-explicit:

- `PROSTHETIC_CARDIAC_VALVE`;
- `PROSTHETIC_MATERIAL_FOR_CARDIAC_VALVE_REPAIR`;
- `PREVIOUS_INFECTIVE_ENDOCARDITIS`;
- `UNREPAIRED_CYANOTIC_CONGENITAL_HEART_DISEASE`;
- `REPAIRED_CHD_WITH_RESIDUAL_SHUNT_OR_VALVULAR_REGURGITATION_AT_PROSTHETIC_PATCH_OR_DEVICE`;
- `CARDIAC_TRANSPLANT_WITH_VALVE_REGURGITATION_DUE_STRUCTURALLY_ABNORMAL_VALVE`.

Non-qualifying/unsupported states remain explicit:

- `UNKNOWN` blocks as unknown;
- `NONE_REPORTED` blocks;
- `OTHER_CARDIAC_CONDITION` blocks.

### Deliberately unresolved / excluded CHD edge case

Older AHA/ACC guidance and the current ADA pediatric summary mention a completely repaired congenital defect with prosthetic material/device during the first six months after repair. The current ADA general patient-selection summary does not present that item in the same way.

C2 adult rule 1 therefore **does not automate this six-month repaired-CHD scenario**. It remains a manual/specialist-confirmation case until its current source contract is separately reconciled. This is a deliberate fail-closed scope reduction, not an assertion that prophylaxis is never indicated.

## Scope locked for rule 1

Included:

- adult only, age >=18;
- high-risk cardiac category explicitly selected from the source-exact controlled enum above;
- qualifying dental procedure explicitly confirmed;
- penicillin/amoxicillin allergy explicitly checked;
- oral route explicitly possible;
- current penicillin/amoxicillin exposure explicitly checked;
- exact selected medication presentation resolved server-side from its stable documentary `presentation_id`;
- exact single-ingredient DCI must resolve to `AMOXICILLIN`.

Excluded:

- pediatric dosing;
- allergy alternatives;
- parenteral alternatives;
- post-procedure rescue dosing;
- six-month completely repaired CHD scenario pending separate reconciliation;
- inference from `antecedents_medicaux` or any other free text;
- automatic interpretation of a diagnosis, cardiac letter or physician note;
- automatic selection of an antibiotic when the patient is already taking penicillin/amoxicillin;
- automatic conversion of 2 g into tablet/capsule counts until presentation-strength parsing is separately certified.

## Fail-closed inputs

The rule blocks if any of the following is absent/unsafe:

- age unknown or <18;
- cardiac risk unknown, unsupported or non-qualifying;
- dental procedure eligibility unknown or false;
- penicillin allergy unknown or present;
- any generic free-text medication allergy remains present and unreconciled;
- oral route unknown or impossible;
- current penicillin/amoxicillin exposure unknown or true;
- exact selected presentation not resolvable server-side;
- canonical active ingredient is not exactly `AMOXICILLIN`.

### Generic allergy reconciliation guard

The existing C1 `medication_allergies` list is free text. C2 never tries to infer whether entries such as brand names, abbreviations or spelling variants represent penicillin/amoxicillin allergy.

Therefore, if `medication_allergy_status=PRESENT`, C2 returns `GENERIC_MEDICATION_ALLERGY_REQUIRES_RECONCILIATION` even when the dedicated penicillin state says `NONE_KNOWN`. This is intentionally conservative until allergies have a structured/coded representation.

## Rule output

Only when every gate passes:

- `rule_id = IE_PROPHYLAXIS_ADULT_ORAL_AMOXICILLIN`
- versioned result;
- active ingredient: `AMOXICILLIN`;
- total dose: `2000 mg`;
- single dose;
- administration window: `30–60 minutes before`;
- AHA + ADA source ids attached.

This result is a **clinical suggestion candidate**, not an autonomous prescription. Practitioner validation remains mandatory.

## Durable patient facts implemented

`patient_clinical_contexts` now adds, with additive migration and `UNKNOWN` default:

- `penicillin_allergy_status`;
- `ie_cardiac_risk_category`.

These are factual practitioner-entered states only. They do not create `clinical_ready` and do not store any dose.

Migration: `c2ie0000002`, descending from `c1ctx0000001`.

## Read-only evaluation endpoint implemented

`POST /api/prescriptions/clinical-rules/ie-prophylaxis/evaluate`

The endpoint:

- enforces prescription permission + patient tenant access;
- derives age from `Patient.date_naissance` at the supplied procedure date;
- reads cardiac/allergy facts only from structured patient context;
- accepts only prescription-scoped explicit procedure/route/current-antibiotic facts;
- resolves the selected CNOPS presentation server-side using its stable `presentation_id`;
- maps only exact single-ingredient `AMOXICILLINE` / `AMOXICILLIN` DCI to the rule code;
- blocks unresolved generic medication allergies rather than parsing them;
- returns a rule evaluation only;
- performs no DB write, no ordonnance mutation, no dose autofill and no call to legacy `/safety/check` or `/smart-suggest`.

## Tests implemented

- positive eligible adult rule;
- unknown inputs fail closed;
- non-qualifying/other cardiac context;
- all automated source-exact positive cardiac categories;
- non-qualifying dental procedure;
- penicillin allergy;
- unresolved generic medication allergy;
- current penicillin/amoxicillin exposure;
- pediatric patient blocked;
- unverified/wrong medication identity;
- patient-context defaults + API roundtrip;
- read-only endpoint READY path;
- missing structured context;
- server-side association rejection (amoxicillin/clavulanate);
- request cannot override durable cardiac state;
- missing prescription-scoped facts;
- tenant isolation;
- patient/context non-mutation across evaluation.

## Remaining gates before UI activation

1. Exact-head CI + PostgreSQL migration + patient/document non-regression.
2. BEFORE capture of the current prescription UI at 390/430/768/1280.
3. Written practitioner-facing mockup with no internal certification jargon.
4. UI ownership for transient procedure/route/current-antibiotic facts without polluting durable patient context.
5. UI suggestion card that remains non-autonomous and requires explicit practitioner acceptance.
6. AFTER certification at the same viewports + frontend/backend regressions.
7. Rebase against current master and recertify exact merge candidate.
8. Merge + post-merge CI + canonical closeout.

## Implemented files

- `backend/services/prescription_clinical_rules.py`
- `backend/schemas/prescription_clinical_rules.py`
- `backend/routers/prescriptions.py`
- `backend/models_patient_clinical_context.py`
- `backend/schemas/patient_clinical_context.py`
- `backend/routers/patient_clinical_context.py`
- `alembic/versions/c2ie0000002_add_ie_prophylaxis_patient_context.py`
- `backend/tests/test_prescription_clinical_rule_ie_prophylaxis.py`
- `backend/tests/test_patient_clinical_context_c2.py`
- `backend/tests/test_prescription_c2_ie_evaluation_endpoint.py`

## Current safety state

The rule is callable only through a read-only evaluation endpoint. No existing prescription UI calls it. No ordonnance is mutated, no dose is inserted, and legacy smart-suggest/safety logic remains disconnected from the Prescription Intelligence V1 UI flow.

## Next exact

Certify the exact backend candidate. If green, capture the current prescription UI BEFORE at 390/430/768/1280 and design the practitioner-facing read-only suggestion flow. Do not implement pediatric, alternative-antibiotic or unresolved six-month repaired-CHD branches in this lot.
