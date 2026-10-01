# Neo-Ordonnance N4.3B — Procedure-Sensitive Safety Evidence Matrix

Date: 2026-10-01  
Branch: `feat/neo-n4-3b-procedure-safety`  
Status: evidence-backed contract + bounded backoffice runtime for procedure taxonomy, antithrombotic bleeding review, IE orchestration and MRONJ prevention review.

## Goal

Add procedure-sensitive safety to Neo-Ordonnance without building a parallel pharmacology engine.

N4.3B must combine:

1. the planned dental procedure;
2. structured current medication / medical context;
3. existing bounded clinical rules;
4. explicit fail-closed states when information is incomplete.

It must never silently advise stopping anticoagulants, antiplatelets or antiresorptive treatment.

## Sources reviewed

### Bleeding / antithrombotics

- SDCEP, *Management of Dental Patients Taking Anticoagulants or Antiplatelet Drugs*, 2nd edition, March 2022.
  - https://www.sdcep.org.uk/published-guidance/anticoagulants-and-antiplatelets/
  - https://www.sdcep.org.uk/media/ypnl2cpz/sdcep-management-of-dental-patients-taking-anticoagulants-or-antiplatelet-drugs-2nd-edition.pdf
- ADA, *Oral Anticoagulant and Antiplatelet Medications and Dental Procedures*, reviewed 2022.
  - https://www.ada.org/resources/ada-library/oral-health-topics/oral-anticoagulant-and-antiplatelet-medications-and-dental-procedures

### Infective endocarditis

- ADA, *Antibiotic Prophylaxis Prior to Dental Procedures*, current page reviewed 2026-10-01.
  - https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis
- AHA scientific statement referenced by ADA: Wilson WR, et al. *Prevention of Viridans Group Streptococcal Infective Endocarditis*, Circulation, 2021.

### MRONJ

- AAOMS, *Medication-Related Osteonecrosis of the Jaw — 2022 Update*.
  - https://aaoms.org/wp-content/uploads/2024/03/mronj_position_paper.pdf
- ADA, *Osteoporosis Medications and Medication-Related Osteonecrosis of the Jaw*.
  - https://www.ada.org/resources/ada-library/oral-health-topics/osteoporosis-medications
- ADA, *Oncology Agents and Medication-Related Osteonecrosis of the Jaw*.
  - https://www.ada.org/resources/ada-library/oral-health-topics/oncology-agents-and-medication-related-osteonecrosis-of-the-jaw

## Evidence matrix

### A. Dental procedure bleeding-risk class

Use the SDCEP procedure classification as the initial deterministic taxonomy.

#### `UNLIKELY_TO_CAUSE_BLEEDING`

Examples:
- local anaesthesia by infiltration, intraligamentary or mental nerve block;
- inferior dental / other regional nerve block;
- basic periodontal examination;
- supragingival plaque/calculus/stain removal;
- restorations with supragingival margins;
- orthograde endodontics;
- impressions / prosthetic procedures;
- fitting or adjustment of orthodontic appliances.

Default Neo behavior:
- no antithrombotic interruption suggestion;
- no bleeding alert solely because antithrombotic therapy is present;
- preserve drug-interaction safety already owned elsewhere.

#### `LOW_POSTOP_BLEEDING_RISK`

Examples:
- simple extraction of 1–3 teeth with restricted wound size;
- incision and drainage of intra-oral swelling;
- detailed six-point periodontal examination;
- root surface debridement;
- restorations with subgingival margins.

Default Neo behavior:
- identify antithrombotic class and combinations;
- surface local haemostasis planning when relevant;
- do not recommend stopping therapy automatically.

#### `HIGHER_POSTOP_BLEEDING_RISK`

Examples:
- complex extractions;
- adjacent extractions causing a large wound;
- >3 extractions at once;
- flap raising procedures, including surgical extraction, periodontal surgery, preprosthetic surgery, periradicular surgery, crown lengthening and implant surgery;
- gingival recontouring;
- biopsies.

Important source nuance:
SDCEP explicitly says “higher risk” does not mean medically high-risk surgery; individual invasiveness still requires practitioner judgement.

Default Neo behavior:
- require complete medication context before giving a procedural safety state;
- elevate to practitioner review when drug-specific timing/INR/prescriber input may matter;
- never autonomously interrupt antithrombotic therapy.

## B. Anticoagulant / antiplatelet contract

### Required structured inputs

- `antithrombotic_status`: UNKNOWN | NONE_REPORTED | PRESENT
- `antithrombotic_agents[]`
- `antithrombotic_classes[]`: VKA | DOAC | ANTIPLATELET | LMWH | OTHER
- `combination_therapy`: UNKNOWN | NO | YES
- `warfarin_inr`: number | null
- `warfarin_inr_checked_at`: datetime | null
- `lmwh_dose_class`: UNKNOWN | PROPHYLACTIC | TREATMENT
- `procedure_bleeding_risk`: UNKNOWN | UNLIKELY_TO_CAUSE_BLEEDING | LOW_POSTOP_BLEEDING_RISK | HIGHER_POSTOP_BLEEDING_RISK

### Fail-closed matrix

- procedure risk UNKNOWN + antithrombotic PRESENT → `REVIEW_REQUIRED`
- medication identity/class UNKNOWN → `REVIEW_REQUIRED`
- anticoagulant + antiplatelet combination → `PRESCRIBER_REVIEW_REQUIRED`
- VKA + invasive procedure + INR absent/stale → `REVIEW_REQUIRED`
- VKA + INR >= 4 → `DO_NOT_PROCEED_ROUTINELY` for invasive care; urgent care requires escalation
- LMWH treatment dose or dose unknown → `PRESCRIBER_REVIEW_REQUIRED`
- DOAC + low-risk procedure → no automatic interruption recommendation
- DOAC + higher-risk procedure → Neo may present a source-backed review prompt, but must not change dose timing by itself
- single/dual antiplatelet therapy → no automatic interruption recommendation

### Explicit prohibition

Neo must not produce:
- “stop aspirin/warfarin/DOAC”;
- “skip the dose”;
- “hold for 24/48 h”;
without an explicit clinician-authored workflow and appropriate prescriber/clinical context.

The app may state that a source-backed procedural review is required and explain why.

## C. Infective endocarditis prophylaxis

### Existing reusable implementation

Reuse:
- `backend/services/prescription_clinical_rules.py`
- `IE_PROPHYLAXIS_ADULT_ORAL_AMOXICILLIN`

The existing rule already requires:
- adult age;
- explicit qualifying cardiac risk category;
- explicit dental procedure eligibility;
- known penicillin allergy status;
- no unresolved generic medication allergy;
- oral route feasibility;
- current penicillin/amoxicillin exposure status;
- verified presentation;
- selected active ingredient = AMOXICILLIN.

### Cardiac categories supported by current ADA/AHA recommendations

Highest-risk categories include:
- prosthetic cardiac valves, including transcatheter prostheses/homografts;
- prosthetic material used for cardiac valve repair;
- previous infective endocarditis;
- cardiac transplant with valve regurgitation caused by a structurally abnormal valve;
- unrepaired cyanotic congenital heart disease;
- repaired congenital heart defect with residual shunt or valvular regurgitation at/adjacent to prosthetic patch/device.

### Qualifying dental procedure

For an otherwise eligible high-risk cardiac patient, prophylaxis applies to dental procedures involving:
- manipulation of gingival tissue;
- manipulation of the periapical region;
- perforation of oral mucosa.

### N4.3B decision

Do not rebuild the IE rule.

Add only:
1. structured procedure eligibility derived from a bounded procedure taxonomy;
2. an adapter/orchestrator that feeds the existing rule;
3. tests proving no prophylaxis recommendation when cardiac risk or procedure eligibility is UNKNOWN/non-qualifying;
4. practitioner-facing wording without internal blocker codes.

The existing rule is adult-only. Pediatric IE prophylaxis remains out of scope unless separately sourced and implemented.

## D. MRONJ contract

### Evidence-backed principles

AAOMS/ADA support distinguishing at least:
- nonmalignant disease / osteoporosis antiresorptive therapy;
- malignant disease with antiresorptive and/or targeted therapies;
- extent/invasiveness of surgery;
- duration/schedule of therapy;
- comorbidities and concurrent therapies;
- active oral infection/inflammation.

AAOMS states:
- for most patients treated for nonmalignant disease, routine operative plans are not automatically altered;
- for malignant disease, MRONJ risk is higher and dentoalveolar surgery should be avoided when possible;
- implant placement is contraindicated in the malignant-disease prevention table;
- drug holidays remain controversial;
- CTX/bone-turnover markers are not validated for MRONJ risk decision-making.

ADA similarly states that routine treatment should not automatically be modified solely because of osteoporosis antiresorptive medication and that evidence is insufficient to recommend a routine drug holiday or CTX-based risk prediction.

### Required structured inputs

- `mronj_medication_status`: UNKNOWN | NONE_REPORTED | PRESENT
- `mronj_agent_class`: BISPHOSPHONATE | DENOSUMAB | ROMOSOZUMAB | ANTIANGIOGENIC | OTHER | UNKNOWN
- `mronj_indication`: OSTEOPOROSIS_NONMALIGNANT | MALIGNANCY | OTHER | UNKNOWN
- `mronj_route`: ORAL | PARENTERAL | UNKNOWN
- `mronj_duration_months`: number | null
- `mronj_concurrent_risk_therapy[]`: CHEMOTHERAPY | STEROID | ANTIANGIOGENIC | OTHER
- `active_oral_infection_or_inflammation`: UNKNOWN | NO | YES
- `procedure_osseous_injury_class`: UNKNOWN | NO_OSSEOUS_INJURY | DENTOALVEOLAR_OSSEOUS_INJURY

### Bounded behavior

- all MRONJ medication/context fields absent or UNKNOWN for an osseous procedure → `REVIEW_REQUIRED`
- osteoporosis/nonmalignant indication + osseous procedure → `MRONJ_CONTEXT_REVIEW`, not an automatic contraindication
- malignant indication + dentoalveolar osseous procedure → `SPECIALIST_OR_PRESCRIBER_REVIEW_REQUIRED`
- malignant indication + implant surgery → hard practitioner-facing warning based on AAOMS prevention guidance
- suspected/known MRONJ → this N4.3B prevention gate is not a treatment algorithm; refer to dedicated specialist workflow
- no automatic drug holiday recommendation
- no CTX-based clearance or “safe threshold”

## E. Minimal target contract

Recommended new bounded type:

```ts
type DentalProcedureBleedingRisk =
  | 'UNKNOWN'
  | 'UNLIKELY_TO_CAUSE_BLEEDING'
  | 'LOW_POSTOP_BLEEDING_RISK'
  | 'HIGHER_POSTOP_BLEEDING_RISK';

type DentalProcedureOsseousRisk =
  | 'UNKNOWN'
  | 'NO_OSSEOUS_INJURY'
  | 'DENTOALVEOLAR_OSSEOUS_INJURY';

interface DentalProcedureSafetyContext {
  bleedingRisk: DentalProcedureBleedingRisk;
  ieProcedureQualifies: boolean | null;
  osseousRisk: DentalProcedureOsseousRisk;
}
```

This procedure context should be separate from medication/patient facts but combined by a bounded orchestrator.

## F. Architecture decision

N4.3B should not create a second pharmacology engine.

Preferred flow:

`procedure taxonomy + Neo N2 patient context + medication identity -> procedure-safety orchestrator -> existing IE rule + bounded bleeding gate + bounded MRONJ gate -> practitioner-facing review state`

Responsibilities remain separated:

- `DentalPharmacologyArbiter`: therapeutic/regimen arbitration;
- N4.2: bounded medication interaction/contraindication supplement;
- existing IE rule: infective-endocarditis prophylaxis;
- N4.3B bleeding gate: procedure x antithrombotic context;
- N4.3B MRONJ gate: procedure x at-risk therapy context.

## G. Safety states exposed to UI

Do not expose internal codes.

Recommended practitioner-facing states:

- `READY` — no procedure-specific blocker identified from complete structured context.
- `CONTEXT_REQUIRED` — required medication/procedure information is missing.
- `CLINICAL_REVIEW_REQUIRED` — source-backed review is required before proceeding.
- `PRESCRIBER_REVIEW_REQUIRED` — medication management may require the prescribing clinician.
- `SPECIALIST_REVIEW_REQUIRED` — higher-risk MRONJ or other specialist-managed scenario.

No N4.3B state should claim that treatment is globally “safe”.

## H. Scientific limitations / release boundary

- These sources are international (US/UK) and do not constitute Morocco-specific regulatory validation.
- No Morocco-specific national dental guidance covering these three domains was established in this review.
- SDCEP DOAC recommendations explicitly include low/very-low certainty evidence in several branches; N4.3B must preserve that uncertainty and avoid over-automation.
- AAOMS states its MRONJ paper is informational and not a substitute for individual clinical judgement.
- Clinical release still requires qualified dental/pharmacology review and Morocco-specific validation where applicable.

## Implementation status

Completed in the current N4.3B branch:
1. `DentalProcedureSafetyContext` + deterministic procedure taxonomy;
2. durable backoffice-only antithrombotic patient facts;
3. IE procedure eligibility wired through the existing IE rule, with no duplicate dosing logic;
4. bounded bleeding gate with no autonomous medication interruption;
5. read-only backoffice endpoint exposing only generic workflow status/alert key;
6. positive/negative/UNKNOWN and tenant-isolation tests for this slice.

Completed MRONJ slice:
1. durable backoffice-only MRONJ exposure/context facts;
2. bounded prevention gate with no diagnosis, no drug-holiday recommendation and no CTX clearance;
3. malignant-disease + osseous/implant scenarios escalate to generic specialist review;
4. osteoporosis/nonmalignant + osseous scenarios escalate to generic clinical review;
5. suspected/known MRONJ exits the prevention gate into specialist review rather than a treatment algorithm;
6. endpoint remains read-only and exposes only generic workflow status/alert keys.

Still pending:
1. final N4.3B exact-head CI/Alembic and adversarial review;
2. subtle practitioner notification wiring only if product validation keeps that surface;
3. no integration to master until the entire Neo-Ordonnance chantier closes.
