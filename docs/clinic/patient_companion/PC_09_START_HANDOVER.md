# PC-09 — Teleconsultation — START HANDOVER

Status: IMPLEMENTATION COMPLETE — CERTIFICATION IN PROGRESS
Base: master after PC-08 POST-MERGE VERIFIED closeout
Previous lot: PC-08 — Secure Messaging
Deployment: none

## Canonical scope
Roadmap source: `docs/clinic/patient_companion/PATIENT_COMPANION_CANONICAL.md`.

Next canonical lot:
- PC-09 — Teleconsultation.

## Inherited doctrine
- cabinet remains the clinical source of truth;
- Patient Companion remains local-first and privacy-preserving;
- zero LLM runtime;
- no Firebase/SaaS plaintext clinical data plane;
- no Vercel deployment without explicit authorization;
- no implementation before audit of existing remote/video primitives.

## Mandatory first audit
Before implementing Teleconsultation, inspect and map:
- any existing video/audio consultation code or dependencies;
- current Patient Companion remote transport and identity binding;
- authentication, tenant/patient binding and revocation;
- browser/device permissions for camera and microphone;
- whether any signaling/STUN/TURN infrastructure already exists;
- encryption boundaries and metadata exposure;
- consent and medico-legal requirements;
- call state truth: ringing/connected/ended/failed;
- offline and reconnect behavior;
- mobile/web compatibility;
- audit logging and retention;
- accessibility and fallback behavior;
- whether recording is absent, optional or prohibited;
- whether appointment context can safely launch a consultation.

## Safety / truth rules
- never claim connected before an authoritative session state exists;
- no silent recording;
- no clinical media through generic push payloads;
- no hidden second source of truth;
- revoked access must terminate future remote access;
- explicit camera/microphone permission boundaries;
- fail closed on identity or transport mismatch.

## Goal / Success / Proof to lock after audit
Goal:
Provide a privacy-preserving patient↔cabinet teleconsultation flow through Patient Companion with truthful session state, explicit permissions and exact identity binding.

Success must become observable and cover at minimum:
- exact patient/tenant/staff binding;
- secure signaling/media boundary;
- explicit camera/microphone consent;
- truthful call lifecycle states;
- reconnect/failure behavior;
- revocation behavior;
- auditability;
- responsive patient and cabinet UX;
- no recording unless explicitly designed and authorized.

Proof must include:
- architecture map;
- backend/permission tests where applicable;
- transport/session lifecycle tests;
- frontend truth-boundary tests;
- BEFORE / target / AFTER evidence on relevant mobile and desktop viewports;
- exact-head CI;
- adversarial review;
- human visual approval before merge.

## Previous lot proof
PC-08:
- human visual gate approved;
- runtime run `35859746972`: SUCCESS;
- PR #677 merged as `6a785791d50d32305a0b7fcde4bc0bd8bcb62f05`;
- post-merge product-file identity verified;
- no Vercel deployment.

## Next exact
1. audit existing teleconsultation/video/audio primitives;
2. write the PC-09 architecture map;
3. identify gaps and fail-closed requirements;
4. lock exact PC-09 Goal / Success / Proof;
5. only then implement the minimal safe flow;
6. certify exact-head + visual;
7. human gate;
8. merge / post-merge / closeout.

No PC-09 implementation is claimed by this handover.


## Audit closeout — 2026-09-23

Verified:
- no existing WebRTC/getUserMedia/WebSocket/STUN/TURN implementation in repo;
- Patient Companion identity/access/revocation can be reused;
- existing signed/encrypted remote command channel is control/signaling capable but is not a real-time media transport;
- appointment opaque references can safely provide optional session context;
- no recording is part of PC-09.

Architecture locked in:
`docs/clinic/patient_companion/PC_09_TELECONSULTATION_ARCHITECTURE_MAP.md`

Implementation decision:
- canonical session state in cabinet DB;
- encrypted authenticated signaling/control;
- WebRTC for media;
- configurable ICE servers;
- explicit camera/microphone permission;
- connected UI only from actual peer connection state;
- no recording;
- no Vercel deployment.

Known external gate:
- no controlled TURN service is currently configured, so reliable arbitrary off-network media cannot yet be certified.

Next exact:
1. implement session model/state machine and authorization;
2. implement signaling contract;
3. implement patient/staff WebRTC UI with explicit permissions;
4. certify deterministic app behavior;
5. stop only at TURN/network E2E gate or human visual gate.


## Audit outcome — 2026-09-23

Verified:
- no existing WebRTC/getUserMedia/RTCPeerConnection/WebSocket media implementation in the repo;
- no existing STUN/TURN configuration or teleconsultation vendor SDK;
- existing Patient Companion remote transport is suitable for authenticated control/signaling, not for audio/video media transport;
- existing access/identity/revocation model is reusable;
- appointment references may be reused as optional context;
- no recording primitive exists.

Architecture locked in:
`docs/clinic/patient_companion/PC_09_TELECONSULTATION_ARCHITECTURE_MAP.md`

Implementation direction:
- WebRTC media plane;
- Patient Companion access-bound control/signaling;
- explicit permissions;
- truthful lifecycle;
- no recording;
- injectable ICE config;
- production readiness blocked until TURN is provisioned and validated.

Next exact:
1. implement the minimal PC-09 session domain + lifecycle;
2. add staff/patient entry points;
3. add WebRTC signaling + media flow behind injectable ICE config;
4. test permission/revocation/failure truth boundaries;
5. certify runtime + visual;
6. human gate;
7. merge / post-merge.


## Implementation checkpoint — 2026-09-23

Implemented and code-reviewed:
- canonical session lifecycle with `CREATED` pre-join truth;
- patient does not see a session until staff has actually joined;
- explicit patient `Accepter et rejoindre` consent wording;
- explicit patient `Refuser` transition;
- WebRTC media plane with no recording;
- provider-agnostic short-lived coturn-compatible credentials;
- direct connectivity remains available; TURN is automatic ICE fallback when configured;
- real peer failure persists canonical `FAILED`;
- signal rows purged on end/reject/failure and observed expiry;
- media fails closed on session-control loss;
- staff start failures stop acquired media resources.

Remaining app gates:
1. exact-head PC-09 certification;
2. exact-head PostgreSQL Alembic schema certification;
3. exact-head CI;
4. runtime AFTER visual evidence;
5. human visual approval;
6. merge / post-merge.

External remote-production gate remains separate:
- controlled reachable TURN endpoint;
- distinct-network + forced-relay E2E;
- measured signaling/reconnect behavior.

No Vercel deployment.
