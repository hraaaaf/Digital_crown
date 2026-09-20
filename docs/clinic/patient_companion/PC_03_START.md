# PC-03 — Medical Questionnaires — START

Status: IN PROGRESS

Base: master@956cbcc6598baf3ce5b8074856312132e6752471
Branch: feature/patient-companion-pc03-medical-questionnaires
Deployment: none

## Goal
Allow an authorized Patient Companion identity to complete a cabinet-issued medical questionnaire securely, without directly mutating the canonical clinical record.

## Success
- questionnaire definitions are cabinet-scoped and versioned;
- patient receives only active questionnaires for its authorized context;
- submission is immutable, tenant-scoped, attributable to the Patient Companion access and questionnaire version;
- submission never auto-writes `Patient.antecedents_medicaux`;
- cabinet review state is explicit: PENDING_REVIEW / REVIEWED / REJECTED;
- no clinical scoring, diagnosis, contraindication inference or automated treatment decision;
- remote/offline semantics never present an unsent questionnaire as received by the cabinet;
- exact-head backend/frontend/schema/security gates pass;
- UI BEFORE/AFTER evidence uses the same mobile viewports.

## Verified anti-duplication audit
- canonical patient source remains `patients`;
- current medical-history storage is `Patient.antecedents_medicaux` free text;
- no existing questionnaire/anamnesis engine was found under the obvious repository terms;
- Patient Companion already provides encrypted local vault + authenticated/opaque remote transport;
- therefore PC-03 adds a reviewable intake layer, not a second patient record.

## Safety contract
Patient answers are patient-reported data pending clinician review. The system must not promote them into verified clinical facts automatically.

## Proof plan
1. schema/model tests;
2. tenant/auth/access isolation tests;
3. questionnaire version + immutable submission tests;
4. frontend state tests;
5. BEFORE/AFTER 360x800 and 390x844 Chromium/WebKit;
6. general CI + PostgreSQL/Alembic + Patient/Portability/T2 + Remote Transport as applicable.
