# PC-07 — Emergency Photo — START HANDOVER

Status: START READY — AUDIT BEFORE IMPLEMENTATION
Branch: feature/patient-companion-pc07-emergency-photo
Base: master@b4e40fa1f3a63d4d7bf4d91223fa376902dcd7a2
Previous lot: PC-06 Patient Finance
PC-06 PR: #645
PC-06 merge commit: b4e40fa1f3a63d4d7bf4d91223fa376902dcd7a2
Deployment: none

## Canonical scope
Roadmap source: `docs/clinic/patient_companion/PATIENT_COMPANION_CANONICAL.md`.

Next canonical lot:
- PC-07 — Emergency Photo.

This file intentionally does not invent product behavior beyond that roadmap label. Exact UX, data contract, lifecycle and permissions must be derived from an audit of existing Digital Crown photo/media primitives.

## Product doctrine inherited
- cabinet remains the clinical source of truth;
- Patient Companion remains local-first and privacy-preserving;
- zero LLM runtime;
- remote Patient Companion operations must use the already-certified secure transport path;
- no Firebase/SaaS plaintext clinical data plane;
- no clinical payload in generic OS notifications or WhatsApp;
- no Vercel deployment without explicit authorization.

## Mandatory first audit
Before implementing Emergency Photo, inspect and map:
- existing patient photo/media models, routes and storage;
- existing camera/upload flows in the cabinet UI;
- media ownership and tenant/patient isolation;
- remote transport support for binary/media workflows, if any;
- document/share permissions and revocation semantics that could be reused;
- local Patient Companion vault behavior for media metadata/binary content;
- image deletion/retention/archive rules;
- MIME/type/size validation and unsafe-file protections;
- EXIF/location metadata handling;
- browser/mobile camera permissions and capture behavior;
- offline/retry semantics;
- audit trail / ACK requirements for a patient-originated upload;
- any existing emergency/urgent clinical workflow.

## Safety / truth rules
- never claim a photo reached the cabinet until durable authoritative ACK exists;
- no optimistic delivered/received state;
- exact tenant + patient binding is mandatory;
- patient-originated media must not silently become a clinical diagnosis;
- no LLM/image interpretation;
- strip or explicitly handle sensitive metadata such as location EXIF before remote persistence unless a verified product requirement says otherwise;
- no public media URL;
- revocation must cut future access;
- failed upload must not overwrite or corrupt the patient's local evidence.

## Goal / Success / Proof to lock after audit
Goal:
Allow a patient to capture/send an emergency photo through Patient Companion while preserving source-of-truth, privacy, transport integrity and explicit delivery state.

Success must become observable and cover at minimum:
- exact patient/tenant ownership;
- durable cabinet ACK before `received` state;
- safe media validation;
- no public/raw storage exposure;
- deterministic retry/idempotency behavior;
- revocation and deletion semantics;
- mobile camera/upload UX;
- offline/failure truthfulness.

Proof must include:
- backend contract + permission tests;
- remote transport/media tests;
- failure/idempotency/retry tests;
- frontend truth-boundary tests;
- BEFORE / target / AFTER evidence on 360x800 and 390x844, Chromium + WebKit;
- exact-head CI;
- adversarial review;
- human visual approval before merge.

## Next exact
1. audit existing image/media/photo primitives and remote transport compatibility;
2. write `PC_07_EMERGENCY_PHOTO_ARCHITECTURE_MAP.md`;
3. identify contradictions/gaps and fail-closed requirements;
4. lock exact PC-07 Goal / Success / Proof;
5. only then implement the minimal safe flow;
6. certify exact-head + visual;
7. human gate;
8. merge / post-merge / PC-08.

No implementation is claimed by this handover.
