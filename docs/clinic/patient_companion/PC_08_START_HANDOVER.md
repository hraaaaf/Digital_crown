# PC-08 — Secure Messaging — START HANDOVER

Status: START READY
Target base: master after PC-07 POST-MERGE VERIFIED closeout
Previous lot: PC-07 — Emergency Photo
Deployment: none

## Canonical scope
Roadmap source: `docs/clinic/patient_companion/PATIENT_COMPANION_CANONICAL.md`.

Next canonical lot:
- PC-08 — Secure Messaging.

This handover intentionally does not invent messaging behavior before auditing existing communication, notification, Patient Companion remote transport, consent, audit and retention primitives.

## Product doctrine inherited
- cabinet remains the clinical source of truth;
- Patient Companion remains local-first and privacy-preserving;
- zero LLM runtime;
- remote Patient Companion operations must use the certified secure transport path;
- no Firebase/SaaS plaintext clinical data plane;
- WhatsApp remains non-canonical and must not carry clinical payload;
- no Vercel deployment without explicit authorization.

## Mandatory first audit
Before implementing Secure Messaging, inspect and map:
- existing Patient Companion remote transport contracts and relay constraints;
- any current staff/patient messaging or communication models/routes;
- notification surfaces and generic OS notification payload rules;
- identity, tenant/patient binding and revocation semantics;
- audit-log requirements for sent/read/failed states;
- local encrypted Patient Companion storage available for message metadata/content;
- retention/deletion/archive requirements;
- attachment/media behavior and whether PC-07 primitives can be reused safely;
- offline/retry/idempotency rules;
- rate limiting / abuse / message-size limits;
- staff-side inbox/thread UX primitives, if any;
- access control and role permissions;
- whether read receipts are authoritative, optional or unsupported;
- encryption boundary and key lifecycle;
- any medico-legal export/evidence requirements.

## Safety / truth rules
- never claim delivered/read without an authoritative corresponding proof;
- no optimistic delivered/read state;
- exact tenant + patient binding is mandatory;
- no clinical plaintext in generic push payloads;
- no WhatsApp clinical content;
- no LLM-generated or interpreted clinical messages;
- no hidden second source of truth;
- revoked access must cut future remote access;
- retries must be deterministic and idempotent;
- failed sends must not erase local evidence of the attempt.

## Goal / Success / Proof to lock after audit
Goal:
Provide secure patient↔cabinet messaging through Patient Companion using the certified remote transport while preserving source-of-truth, confidentiality, identity binding and truthful delivery state.

Success must become observable and cover at minimum:
- exact patient/tenant/staff binding;
- encrypted transport and storage boundaries;
- deterministic send/retry/idempotency behavior;
- truthful pending/sent/delivered/read states according to available authoritative evidence;
- revocation behavior;
- safe offline behavior;
- auditability;
- mobile UX and cabinet UX;
- no plaintext clinical payload outside trusted boundaries.

Proof must include:
- backend contract + permission tests;
- remote transport tests;
- replay/idempotency/retry/failure tests;
- local encrypted-storage tests if message content is cached locally;
- frontend truth-boundary tests;
- BEFORE / target / AFTER evidence at 360x800 and 390x844, Chromium + WebKit where relevant;
- exact-head CI;
- adversarial review;
- human visual approval before merge.

## Next exact
1. verify PC-07 post-merge closeout and merge docs PR;
2. audit current messaging/notification/transport primitives;
3. write `PC_08_SECURE_MESSAGING_ARCHITECTURE_MAP.md`;
4. identify contradictions/gaps and fail-closed requirements;
5. lock exact PC-08 Goal / Success / Proof;
6. only then implement the minimal safe flow;
7. certify exact-head + visual;
8. human gate;
9. merge / post-merge / next lot.

No implementation is claimed by this handover.
