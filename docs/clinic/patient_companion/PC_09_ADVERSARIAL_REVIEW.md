# PC-09 — Teleconsultation — Adversarial Review

Status: APP FINDINGS RESOLVED — EXTERNAL REMOTE-NETWORK GATE REMAINS
Date: 2026-09-23

## Scope reviewed
- canonical session model and lifecycle;
- access / tenant / patient binding;
- Patient Companion remote-operation registry;
- signaling persistence and bounds;
- patient and staff WebRTC UI;
- media permission boundary;
- connection truth;
- visual evidence plan;
- remote-network assumptions.

## Verified strengths

### Identity and isolation
- every patient remote action is scoped through the existing active PatientCompanionAccess;
- staff routes resolve the cabinet patient first and then require an active access belonging to the same employer + patient;
- session rows are access + employer + patient scoped;
- cross-access session lookup fails closed;
- revoked Patient Companion access blocks new patient remote commands.

### Truthful call state
- signaling alone does not set CONNECTED;
- both patient and staff must independently report an actual browser RTCPeerConnection state of connected;
- canonical CONNECTED is written only when both reports exist;
- terminal states do not revive;
- sessions expire.

### Permissions / media
- patient copy now uses explicit `Accepter et rejoindre` before camera/microphone permission;
- patient can explicitly `Refuser` without activating media;
- staff media permission/start failure closes local tracks/peer resources;
- no MediaRecorder path exists;
- no audio/video payload is persisted in Digital Crown;
- local tracks are stopped and RTCPeerConnection is closed on cleanup/end.

### Signaling bounds
- signaling payload size is bounded;
- sync batches are bounded;
- a real JOSE relay-envelope size test is included;
- current UI uses non-trickle ICE so it does not flood the command relay with one remote command per ICE candidate.

## Adversarial findings

### A1 — Existing Patient Companion relay is not a real-time signaling transport
Severity: BLOCKING for claiming reliable remote teleconsultation.

The existing remote transport is intentionally command/ACK:
- encrypted envelope pushed to a relay mailbox;
- cabinet worker processes it;
- patient side polls for the encrypted ACK;
- sendViaRelay may wait/poll for the response.

This is appropriate for agenda, messaging, consent and other asynchronous operations.
It is not yet evidence of low-latency real-time signaling suitable for arbitrary remote WebRTC negotiation/recovery.

Decision:
- keep the implementation and deterministic contracts;
- do NOT claim production-grade off-network teleconsultation until a real-time signaling path or measured relay latency budget is designed and certified.

### A2 — No controlled TURN service/configuration exists
Severity: BLOCKING for arbitrary off-network media reliability.

Current browser peer configuration intentionally has no hard-coded third-party ICE/TURN service.
Direct connectivity can work in permissive/local networks but cannot be claimed across restrictive NAT/firewall environments.

Correction implemented in candidate:
- TURN configuration is provider-agnostic;
- credentials are generated server-side using coturn-compatible time-limited HMAC credentials;
- the shared TURN secret is never returned to clients;
- no third-party TURN URL or credential is hard-coded.

Remaining external gate:
- no controlled TURN server is deployed/configured yet;
- remote-network E2E must include at least one forced-relay TURN scenario before production certification.

### A3 — Signaling metadata retention
Severity: RESOLVED in app candidate.

SDP/ICE signaling can expose networking metadata. It is not clinical media, but unnecessary long-term retention is undesirable.

Verified correction:
- signaling rows are purged on explicit end;
- signaling rows are purged on patient reject;
- signaling rows are purged on peer failure;
- expired-session cleanup purges signaling when the session is observed.

### A4 — Visual proof cannot prove media-network reliability
Severity: EXPECTED.

Playwright visual evidence can prove:
- UI visibility;
- permission wording;
- responsive geometry;
- no overflow;
- truthful waiting/available states.

It must not be presented as proof that a real remote media path works.

## Required gates before merge
1. PC-09 backend/frontend exact-head certification green.
2. PostgreSQL Alembic schema certification green.
3. runtime visual AFTER evidence green at target viewports.
4. app truth/retention corrections preserved on exact-head CI.
5. human visual approval.
6. merge may occur only with PC-09 explicitly classified as local/direct-network capable if real-time signaling + TURN E2E is still missing.

## Gate for full remote certification
Full remote teleconsultation certification requires:
- controlled TURN;
- measured signaling latency/reconnect behavior;
- two-network E2E (patient and cabinet on distinct networks);
- forced TURN-relay test;
- camera/microphone permission denial/retry E2E;
- disconnect/reconnect test;
- proof that CONNECTED never appears before real peer connection.

No Vercel deployment is authorized.


### A5 — Pre-join truth
Severity: RESOLVED.

Original issue:
- staff session creation claimed `staff_joined_at` before camera/microphone/media setup had actually succeeded.

Correction:
- a new session starts `CREATED`;
- `staff_joined_at` remains null at creation;
- patient list hides `CREATED`;
- only the explicit staff join after media setup moves the session to `WAITING_PATIENT`.

### A6 — Peer/control-plane failure truth
Severity: RESOLVED.

Corrections:
- real browser peer `failed` state is persisted as canonical `FAILED`;
- failure codes are allow-listed;
- signaling is purged on failure;
- patient and staff media are stopped when session-control synchronization is lost;
- staff startup failures stop acquired tracks/peer resources.

### A7 — Consent / decline boundary
Severity: RESOLVED.

Corrections:
- patient sees explicit acceptance wording before media permission;
- CTA is `Accepter et rejoindre`;
- separate `Refuser` action exists and does not activate camera/microphone;
- `REJECTED` is now a real terminal transition;
- rejection is restricted to pre-connected states.

### Standards cross-check
- coturn TURN REST authentication design checked against the coturn turnserver documentation: time-limited `timestamp:username` + Base64(HMAC-SHA1(shared-secret, username)).
- browser ICE configuration and camera/microphone permission boundaries checked against MDN `RTCPeerConnection` and `getUserMedia()` documentation.
