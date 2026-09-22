# PC-04 — Consent Vault patient-facing — START

Status: STARTED
Base: master@86fc61a572f303c812f1999c887e35574df0bb49
Branch: feature/patient-companion-pc04-consent-vault
Deployment: none

## Canonical scope
Source of truth: Digital Crown Patient Companion roadmap in Notion.

PC-04 is **Consent Vault patient-facing**.

The validated roadmap context identifies the remaining patient-facing gap as remote document signing and states the success criterion as an **auditable chain of evidence**.

## Goal
Expose a patient-facing consent/signature workflow from the Patient Companion while preserving a verifiable, auditable evidence chain and without weakening the existing local/on-prem security model.

## Success
- patient only sees documents/consents explicitly exposed to their authorized Patient Companion context;
- the patient-facing action is attributable to the authorized access/context;
- signed/acknowledged state is never claimed before durable cabinet acknowledgement;
- evidence remains auditable and version-bound;
- no silent overwrite of the source document/version;
- no automatic clinical interpretation is introduced;
- offline/transport failure cannot be represented as completed;
- exact-head backend/frontend regression gates pass;
- BEFORE/AFTER evidence uses the same mobile viewports as prior Patient Companion lots.

## Anti-duplication gate
Before implementation, inspect existing document, patient-signature and consent-related models/services/UI and reuse them where possible.

No new consent semantics, legal wording, signature standard or retention claim may be invented without repository or external evidence.

## UI/UX protocol
BEFORE → written goal → target → implementation → AFTER at 360x800 and 390x844 on Chromium/WebKit → comparison/tests → severe visual score.

## Next exact
Audit existing signature/document capabilities and identify the minimum integration seam for patient-facing Consent Vault. Do not implement a parallel consent engine if an existing canonical primitive can be reused.
