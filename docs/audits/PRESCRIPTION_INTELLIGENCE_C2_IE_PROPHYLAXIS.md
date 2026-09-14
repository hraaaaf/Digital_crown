# Prescription Intelligence C2 — IE prophylaxis rule 1

Date: 2026-09-15

## Status

ACTIVE — scientific/backend rule contract implemented on an isolated branch. No API endpoint, no UI suggestion and no automatic prescription activation yet.

## Goal

Implement the first narrow, versioned, fail-closed clinical rule for Digital Crown:

**Adult infective endocarditis prophylaxis for an eligible invasive dental procedure using oral amoxicillin.**

Success means:

- the rule never infers eligibility from free text;
- every required input is explicit;
- unknown, conflicting, pediatric, allergic, non-qualifying, wrong-medication or concurrent-penicillin cases block;
- only the fully eligible adult path returns the source-backed regimen;
- the result is traceable to a rule id, rule version and source ids;
- no UI/API activation occurs before structured patient/session inputs exist and the rule is independently reviewed.

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
- exact selected medication identity explicitly coded as `AMOXICILLIN`;
- exact presentation selection explicitly verified.

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
- exact selected presentation not verified;
- canonical active ingredient is not exactly `AMOXICILLIN`.

## Qualifying cardiac categories represented by the rule contract

- prosthetic cardiac valve or prosthetic material used for valve repair;
- previous infective endocarditis;
- qualifying congenital heart disease;
- cardiac transplant with valvulopathy.

The product must not infer one of these categories from narrative text.

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

## Product integration gates before UI activation

1. Add structured durable cardiac-risk category to patient clinical context, with `UNKNOWN` default.
2. Add a dedicated structured penicillin/amoxicillin allergy state; generic free-text allergy matching is not sufficient.
3. Add prescription/session-scoped explicit fields for:
   - qualifying dental procedure;
   - oral route possible;
   - current penicillin/amoxicillin exposure.
4. Derive adult age from `Patient.date_naissance` using the procedure date, not a guessed age string.
5. Bind the rule only to an exact selected `AMOXICILLIN` presentation.
6. Expose the result as a practitioner-reviewed suggestion, never as silent autofill.
7. Add UI BEFORE → mockup → AFTER certification at 390/430/768/1280.
8. Run backend full regression including DB / patients / documents before merge.
9. Independent scientific review before activation.

## Implemented files

- `backend/services/prescription_clinical_rules.py`
- `backend/tests/test_prescription_clinical_rule_ie_prophylaxis.py`

## Current safety state

No route imports or calls this rule yet. No existing prescription flow is modified. Therefore C2 currently cannot emit a practitioner-facing suggestion in production.

## Next exact

Add the missing structured inputs without changing existing patient/document semantics, then expose a read-only evaluation endpoint and UI suggestion card behind the same fail-closed gates. Do not implement pediatric or alternative-antibiotic branches in this lot.
