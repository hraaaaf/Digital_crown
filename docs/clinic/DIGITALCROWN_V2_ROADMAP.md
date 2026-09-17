# Digital Crown — V2 Roadmap

Status: **PARKED / POST-V1 ONLY / NON-EXECUTABLE UNTIL V1_OPERATIONAL**

Effective date: 17 September 2026

## 1. Authority and sequencing

This document records the approved **post-V1** product direction for Digital Crown.

It is **not** an execution roadmap while `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md` remains authoritative and V1 has not reached `V1_OPERATIONAL`.

Rules:

- V1 scope remains unchanged.
- No V2 implementation, migration, rollout, deployment, or cabinet mutation is authorized by this file.
- No V2 work may delay, widen, or contaminate the mandatory V1 lot sequence.
- V2 execution may start only after `V1_OPERATIONAL` is explicitly recorded in the canonical V1 roadmap and a new V2 execution gate is intentionally opened.
- Until then, this file is backlog/product-direction evidence only.
- No Vercel deployment is authorized by this roadmap.

## 2. Product direction

V2 should extend Digital Crown beyond core practice management into a **traceability, evidence, follow-up and clinical-operations layer**.

The central product idea is not to create disconnected mini-apps, but to reuse Digital Crown's existing patient, act, practitioner, document, imaging and timeline context so that every new module is linked to the clinical record.

## 3. Approved V2 modules

### V2-01 — SteriTrace

**Goal:** provide cabinet-level sterilization traceability without requiring proprietary hardware.

Core scope:

- sterilization cycle registry;
- autoclave/device identity;
- operator identity;
- cycle date/time and status;
- load/cassette/instrument-batch association;
- optional QR/DataMatrix identifiers;
- chemical/biological control result capture where applicable;
- attachment of proof/photo/document when needed;
- linkage from sterilization cycle to patient/act and reverse lookup from patient/act to cycle;
- immutable audit/history semantics for traceability records;
- PDF/exportable traceability record.

Explicit non-goals for first V2 implementation:

- proprietary IoT hardware;
- mandatory direct autoclave integration;
- proprietary printers;
- device-vendor lock-in.

### V2-02 — Implant Passport

**Goal:** provide end-to-end traceability for implants and biomaterials used in patient care.

Core scope:

- manufacturer / product / reference;
- lot or serial number;
- dimensions and relevant device attributes;
- expiration date when available;
- implant site/tooth linkage;
- practitioner and procedure linkage;
- associated radiographs/photos/documents;
- biomaterial and component traceability where relevant;
- patient-level implant passport view;
- reverse lookup by lot/reference to identify affected patients;
- exportable implant/device record.

Preferred capture path:

- barcode / QR / DataMatrix scan where technically reliable;
- manual fallback always available.

### V2-03 — Consent Vault

**Goal:** bind the exact consent version signed by a patient to the exact clinical context in which it was used.

Core scope:

- versioned consent templates;
- immutable record of the signed version;
- signature timestamp;
- patient / practitioner / act linkage;
- document integrity metadata;
- pre-act missing-consent warnings where configured;
- retrieval of historical signed versions even after template updates;
- exportable evidence package.

### V2-04 — Post-Op

**Goal:** provide structured postoperative follow-up while keeping clinical judgment human-led.

Core scope:

- procedure-specific follow-up schedules (for example J+1 / J+3 / J+7 where configured);
- structured patient-reported symptoms;
- pain score and symptom tracking;
- optional photo upload;
- medication adherence/check questions where appropriate;
- rules-based flags for practitioner review;
- full linkage to the originating act and patient timeline;
- clinician review/audit trail.

Safety rule:

Post-Op must not autonomously diagnose, prescribe, or represent automated clinical judgment. It may collect, structure and escalate information for human review.

### V2-05 — Referral Loop

**Goal:** prevent referred patients and reports from disappearing outside the cabinet workflow.

Core scope:

- referral creation;
- destination practitioner/specialty;
- reason and related documents;
- referral status timeline;
- appointment/reception/completion/report-return states;
- reminders for unresolved referrals;
- returned report/document attachment;
- patient timeline integration.

### V2-06 — PhotoCase

**Goal:** standardize clinical photography and longitudinal visual comparison.

Core scope:

- configurable photographic protocols;
- standardized intraoral / extraoral shot sets;
- timeline by episode/treatment stage;
- T0 / T1 / T2 comparison;
- before/after alignment and comparison tooling;
- patient/act linkage;
- separation of clinical-storage consent from communication/marketing usage consent;
- export/share controls consistent with privacy rules.

### V2-07 — Evidence Pack

**Goal:** generate a coherent chronological medico-administrative evidence package from data already held by Digital Crown.

Core scope:

- diagnosis and clinical notes;
- imaging and photographs;
- treatment plans / estimates;
- consent versions;
- prescriptions;
- acts/procedures;
- payments and relevant administrative records;
- communications/documents when part of the cabinet record;
- Implant Passport data;
- SteriTrace records;
- chronological manifest;
- timestamped PDF/ZIP export;
- integrity metadata sufficient to establish what was exported and when.

Evidence Pack should be primarily an **assembly/export layer**, not a duplicate data store.

### V2-08 — Equipment Log

**Goal:** maintain operational history for clinically relevant cabinet equipment.

Core scope:

- equipment inventory;
- serial/reference data;
- installation date;
- maintenance schedule;
- interventions and failures;
- maintenance/service documents;
- certificates where relevant;
- reminders;
- linkage to SteriTrace equipment when useful.

Target equipment may include autoclaves, compressors, radiology equipment, chairs and other cabinet-critical devices.

## 4. Coherent V2 capability layers

### Traceability Layer

Primary modules:

- SteriTrace;
- Implant Passport;
- Equipment Log.

Purpose: answer **what was used, on whom, by whom, when, from which lot/device/cycle, and with what supporting record**.

### Evidence Layer

Primary modules:

- Consent Vault;
- Evidence Pack;
- PhotoCase.

Purpose: preserve the exact clinical and medico-administrative evidence surrounding care and make it retrievable in a coherent timeline.

### Continuity Layer

Primary modules:

- Post-Op;
- Referral Loop.

Purpose: reduce loss of clinical continuity after a procedure or when care leaves the cabinet temporarily.

## 5. Preliminary priority after V1

This ordering is a **product preference**, not yet an authorized execution sequence:

1. Implant Passport
2. SteriTrace
3. Consent Vault
4. Evidence Pack
5. Post-Op
6. PhotoCase
7. Referral Loop
8. Equipment Log

Rationale:

- Implant Passport and SteriTrace create the strongest common traceability foundation.
- Consent Vault and Evidence Pack then exploit that foundation for medico-administrative integrity.
- Post-Op, PhotoCase and Referral Loop extend continuity and longitudinal clinical value.
- Equipment Log is useful but should not displace higher-value patient-linked work unless operational evidence justifies reprioritization.

This ordering must be revalidated against the real V1 architecture, user evidence, regulatory constraints and implementation cost after V1 closure.

## 6. V2 architecture principles

When V2 is eventually opened for execution:

- reuse existing Digital Crown patient, practitioner, act, document, media and timeline identities;
- avoid duplicate shadow records when a canonical V1 entity already exists;
- local/on-premise operation remains the default architecture unless an explicit future decision changes it;
- avoid hardware dependencies in first implementations;
- every irreversible or medico-legally relevant record requires explicit history/audit semantics;
- migrations must preserve historical integrity and rollback capability;
- privacy-sensitive exports require explicit user action and traceability;
- clinical automation remains fail-closed when evidence or human review is required;
- visual work must follow the repository's current evidence/certification rules in force at execution time.

## 7. V2 opening gate

V2 remains **PARKED** until all of the following are true:

1. `V1_OPERATIONAL` is explicitly recorded in `DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`;
2. post-V1 master is verified stable;
3. an inventory of V1 entities/APIs/migrations relevant to V2 is completed;
4. regulatory/privacy assumptions for the selected first V2 module are revalidated;
5. a dedicated V2 execution roadmap defines exact lots, success criteria, proof requirements and rollback boundaries;
6. explicit human authorization opens the first V2 lot.

Until that gate is satisfied, this document records **approved product scope only**.

## 8. Current state

- V2 scope: **APPROVED AS POST-V1 PRODUCT DIRECTION**
- V2 modules: **8**
- V2 implementation: **NOT AUTHORIZED**
- V2 migration: **NOT AUTHORIZED**
- V2 deployment: **NOT AUTHORIZED**
- cabinet/production mutation: **NOT AUTHORIZED**
- dependency on V1: **HARD — V1_OPERATIONAL REQUIRED FIRST**
