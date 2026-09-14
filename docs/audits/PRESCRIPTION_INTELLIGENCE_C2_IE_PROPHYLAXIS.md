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

ESC infective-endocarditis guidance independently reports oral amoxicillin **2 g as a single dose 30–60 minutes before** an eligible dental procedure in high-risk patients.

## Scope locked for rule 1

Included:

- adult only, age >=18;
- high-risk cardiac category explicitly selected from a controlled enum;
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
- inference from `antecedents_medicaux` or any other free text;
- automatic interpretation of a diagnosis, cardiac letter or physician note;
- automatic selection of an antibiotic when the patient is already taking penicillin/amoxicillin;
- automatic conversion of 2 g into tablet/capsule counts until presentation-strength parsing is separately certified.

## Fail-closed inputs

The rule blocks if any of the following is absent/unsafe:

- age unknown or <18;
- cardiac risk unknown or non-qualifying;
- dental procedure eligibility unknown or false;
- penicillin allergy unknown or present;
- oral route unknown or impossible;
- current penicillin/amoxicillin exposure unknown or true;
- exact selected presentation not resolvable server-side;
- canonical active ingredient is not exactly `AMOXICILLIN`.

## Qualifying cardiac categories represented by the current rule contract

- prosthetic cardiac valve or prosthetic material used for valve repair;
- previous infective endocarditis;
- qualifying congenital heart disease;
- cardiac transplant with valvulopathy.

The product must not infer one of these categories from narrative text. Exact category wording/coverage remains subject to independent scientific review before UI activation.

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
- returns a rule evaluation only;
- performs no DB write, no ordonnance mutation, no dose autofill and no call to legacy `/safety/check` or `/smart-suggest`.

## Tests implemented

- positive eligible adult rule;
- unknown inputs fail closed;
- non-qualifying cardiac context;
- non-qualifying dental procedure;
- penicillin allergy;
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
2. Independent scientific review of the represented cardiac categories and exact source wording; resolve any AHA/ADA/ESC category-detail divergence before exposing eligibility choices.
3. Decide UI ownership for prescription-scoped facts without persisting transient states into durable patient context.
4. BEFORE capture of the current prescription UI at 390/430/768/1280.
5. Written practitioner-facing mockup with no internal certification jargon.
6. UI suggestion card that remains non-autonomous and requires explicit practitioner acceptance.
7. AFTER certification at the same viewports + frontend/backend regressions.
8. Rebase against current master and recertify exact merge candidate.
9. Merge + post-merge CI + canonical closeout.

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

Certify the exact backend candidate, independently review the cardiac eligibility taxonomy, then design and certify the practitioner-facing read-only suggestion flow. Do not implement pediatric or alternative-antibiotic branches in this lot.
