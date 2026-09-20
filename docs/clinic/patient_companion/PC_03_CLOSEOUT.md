# PC-03 — Medical Questionnaires — CLOSEOUT

Status: CERTIFIED CANDIDATE
Branch: feature/patient-companion-pc03-medical-questionnaires
PR: #640
Certified product HEAD before this closeout commit: 081cd6e04a2bbf29e07d77e8f38cb95af78fae27
Base: master@956cbcc6598baf3ce5b8074856312132e6752471
Deployment: none

## Goal
Allow an authorized Patient Companion identity to complete a cabinet-issued medical questionnaire securely, without directly mutating the canonical clinical record.

## Verified product behavior
- questionnaire definitions are cabinet-scoped and versioned;
- questionnaire assignment is explicit per patient/version;
- patient submission is immutable per assignment;
- patient submission is attributable to the Patient Companion access;
- `Patient.antecedents_medicaux` is never auto-written;
- explicit review states: PENDING_REVIEW / REVIEWED / REJECTED;
- no clinical scoring, diagnosis, contraindication inference or automated treatment decision;
- Patient Companion home remains local-first and performs no implicit questionnaire fetch before explicit online/sync state;
- UI never claims "sent" when transport fails;
- successful submit requires cabinet ACK and returns `clinical_record_updated: false`.

## Exact-head certification — 081cd6e04a2bbf29e07d77e8f38cb95af78fae27
- CI: 35531724428 — SUCCESS
- Patient P7 Final Certification: 35531724387 — SUCCESS
- T2 Runtime Browser Certification: 35531724394 — SUCCESS
- PostgreSQL Alembic Schema Certification: 35531724480 — SUCCESS
- Patient Companion Remote Transport Gate: 35531724423 — SUCCESS
- PC-00 Patient Companion Visual Certification: 35531724431 — SUCCESS
- PC-02 BEFORE Visual Evidence: 35531724442 — SUCCESS
- PC-02 AFTER Visual Evidence: 35531724400 — SUCCESS
- PC-03 BEFORE Visual Evidence: 35531724427 — SUCCESS
- PC-03 AFTER Visual Evidence: 35531724440 — SUCCESS
- Agenda A5 Visual Evidence: 35531724434 — SUCCESS
- M6-I Biometric Passkey Certification: skipped as expected
- PR Merge Summary: skipped as expected

## Visual evidence
BEFORE artifact:
- id: 10611371844
- digest: sha256:baa40a9d0447a980be5b3bc8b54bb51d21f74c4a2107f0d0fb6a942c54211f3f

AFTER artifact:
- id: 10611925644
- digest: sha256:727997996a4143e3c45adc22e6c8d2982f4daa14fd7cff543850a91852eeb98e

Matrix:
- Chromium 360x800
- Chromium 390x844
- WebKit 360x800
- WebKit 390x844
- horizontalOverflow=false on all four BEFORE and all four AFTER captures.

Manual visual review:
- hierarchy remains consistent with Patient Companion shell;
- questionnaire card is clearly separated from agenda and documents;
- patient-reported vs clinician-reviewed distinction is explicit;
- controls remain touch-sized and readable;
- cross-browser rendering is coherent;
- no clipped actions or horizontal overflow observed.

Severe visual score: 8.8/10.
Reserve: opening a multi-question form increases vertical density and page length; acceptable for PC-03, but future polish may consider progressive sections for larger questionnaires.

## Regression findings corrected during certification
1. Literal `\\n` generation defects in Python/TSX source caused compilation failures — fixed.
2. Questionnaire fetch happened before explicit online enable — fixed with fail-closed `enabled` guard.
3. Successful ACK message was cleared by post-submit refresh — fixed.
4. Inherited PC-02 BEFORE harness expected an obsolete exact label — aligned to the certified `Contrôle orthodontique · 30 min` rendering.

## Success criterion
Met for product HEAD 081cd6e04a2bbf29e07d77e8f38cb95af78fae27 with the exact-head runs and artifacts above.

## Merge rule
This closeout commit itself must be recertified on its exact HEAD before PR #640 is marked ready and merged.
