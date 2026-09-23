# PC-09 — Teleconsultation — Architecture Map

Status: AUDIT LOCKED
Date: 2026-09-23
Base: master `e0a9e58c6f0457935684fcd98318ee3726029287`

## 1. Verified repository audit

### Existing capabilities
- Patient Companion already has exact identity/access binding through `PatientCompanionIdentity` + `PatientCompanionAccess`.
- Revocation is represented on both identity/access and remote keysets.
- Existing remote transport is signed + encrypted and validates access, freshness, idempotency and replay.
- Remote command processing is allow-listed by operation prefix and audited.
- Patient local state is encrypted at rest in IndexedDB with a non-exportable AES-GCM device key.
- Agenda already exposes opaque appointment references bound to tenant + patient.
- PC-08 provides secure asynchronous messaging and truthful receipt semantics.

### Missing capabilities
Repository search found no implementation of:
- `navigator.mediaDevices.getUserMedia`;
- `RTCPeerConnection`;
- WebSocket transport;
- STUN/TURN configuration;
- video-call/session models;
- camera/microphone permission UX;
- call lifecycle state machine;
- media recording.

Frontend dependencies contain no dedicated RTC SDK/provider.

## 2. External standards baseline

The browser media layer shall use the WebRTC browser APIs rather than transporting audio/video through the Patient Companion command relay.

Required browser primitives:
- Media Capture and Streams for explicit camera/microphone acquisition;
- WebRTC `RTCPeerConnection` for real-time media;
- secure-context deployment for capture-capable browser surfaces.

No application-level recording is part of PC-09.

## 3. Architectural decision

### Control plane
Reuse Digital Crown canonical Patient Companion identity and authorization.

Create a PC-09 call session bound to:
- `employer_id`;
- `patient_id`;
- `PatientCompanionAccess`;
- optional `PatientCompanionAppointmentRef`;
- staff user;
- opaque session UUID.

The cabinet database remains canonical for session lifecycle.

### Signaling plane
Use authenticated Patient Companion signaling messages only for:
- join/request;
- offer/answer;
- ICE candidate exchange;
- accept/reject/end;
- heartbeat/session expiry.

Signaling must never be treated as proof that media is connected.

The existing signed/encrypted Patient Companion transport may carry signaling control payloads. Its command/ACK semantics are not used as a media transport.

### Media plane
Audio/video media flows only through WebRTC:
- direct peer-to-peer where connectivity permits;
- TURN relay when direct connectivity fails.

No audio/video bytes are persisted in Digital Crown by PC-09.

### ICE / TURN policy
- configurable ICE server list;
- no hard-coded third-party credentials;
- production remote reliability requires a controlled TURN service;
- absence of usable ICE configuration must fail clearly rather than pretending the call is connected.

## 4. Truthful lifecycle

Canonical server session states:
- `CREATED`
- `WAITING_PATIENT`
- `WAITING_STAFF`
- `NEGOTIATING`
- `CONNECTED`
- `ENDED`
- `REJECTED`
- `EXPIRED`
- `FAILED`

Rules:
- `CONNECTED` may only be written after the participating client reports an actual WebRTC peer connection state of `connected` and the peer identity/session binding still matches.
- `NEGOTIATING` is not displayed as connected.
- ended/rejected/expired sessions cannot be revived.
- revoked Patient Companion access immediately blocks new signaling and join attempts.
- stale sessions expire automatically.
- UI must distinguish waiting, connecting, connected, ended and failed.

## 5. Permission boundary

Camera and microphone are requested only after the patient explicitly chooses “Accepter et rejoindre”.

Before browser permission is requested, UI explains:
- camera use;
- microphone use;
- no recording by Digital Crown PC-09.

Permission denial must return to a recoverable state with separate retry controls.

## 6. Appointment binding

An appointment can expose “Téléconsultation” only when a PC-09 session is explicitly created for its opaque appointment reference.

Appointment existence alone never creates or implies a call.

## 7. Staff UX

Minimal cabinet flow:
1. clinician opens patient context;
2. creates/opens a teleconsultation session;
3. waits for the patient;
4. explicit camera/microphone permission;
5. WebRTC negotiation;
6. truthful connected indicator;
7. explicit end call.

No background auto-answer.

## 8. Patient UX

Minimal Patient Companion flow:
1. session appears only for the active paired access;
2. patient explicitly taps “Accepter et rejoindre”;
3. permission explainer;
4. browser camera/microphone prompt;
5. waiting/connecting;
6. connected only on verified peer state;
7. explicit hang-up.

Parent/guardian access is allowed only through an authorized `PatientCompanionAccess` relationship.

## 9. Audit / privacy

Persist:
- session IDs and bindings;
- created/accepted/connected/ended timestamps;
- actor type for lifecycle transitions;
- failure/rejection reason codes;
- no SDP body in generic audit details;
- no ICE credentials in logs;
- no media payload.

## 10. Fail-closed conditions

Reject or terminate when:
- access revoked;
- access/session tenant or patient mismatch;
- session expired;
- actor not authorized;
- malformed/oversized signaling payload;
- invalid lifecycle transition;
- peer session ID mismatch;
- camera/microphone permission missing for requested media;
- WebRTC transport fails.

## 11. Goal / Success / Proof

### Goal
Provide a privacy-preserving patient↔cabinet teleconsultation flow through Patient Companion with exact identity binding, explicit device permissions, WebRTC media, and truthful call state.

### Success
Observable success requires:
1. exact tenant/patient/access/staff binding;
2. session lifecycle enforced server-side;
3. explicit camera/microphone request;
4. signaling isolated from media;
5. WebRTC peer state drives connected truth;
6. revocation blocks join/signaling;
7. no recording;
8. no clinical media in generic push or command payloads;
9. responsive cabinet + patient UX;
10. deterministic expiry/end/failure behavior.

### Proof
- backend session authorization/state-machine tests;
- replay/invalid-transition/revocation tests;
- frontend media permission tests;
- WebRTC truth-boundary tests with deterministic browser mocks;
- signaling contract tests;
- BEFORE / target / AFTER at mobile and desktop viewports;
- exact-head CI;
- adversarial review;
- human visual gate before merge;
- real TURN/network E2E required before claiming reliable off-network remote media.

## 12. Known infrastructure gate

A reliable remote WebRTC call generally needs TURN for restrictive NAT/firewall cases.

Repository audit found no deployed/controlled TURN service. PC-09 now includes provider-agnostic coturn-compatible ephemeral credential generation:
- TURN URLs + shared secret remain server configuration;
- the browser receives only short-lived HMAC-derived credentials;
- the shared secret never leaves the cabinet backend;
- no TURN vendor is hard-coded.

Therefore:
- application/session/signaling implementation can proceed;
- a TURN service can later be connected without redesigning the UI/media contract;
- “reliable remote teleconsultation across arbitrary patient networks” cannot be certified until a controlled TURN endpoint is actually deployed/configured and tested.

No Vercel deployment is authorized.


## 13. Consent / TURN UX decision — 2026-09-23

- The patient explicitly accepts the teleconsultation through the `Accepter et rejoindre` action before browser media permission is requested.
- The UI states that camera and microphone activate only after the patient's action and that PC-09 does not record the consultation.
- TURN/STUN selection is a transport implementation detail and is not presented as a separate patient consent choice.
- WebRTC keeps direct connectivity available and uses configured TURN candidates automatically through ICE when needed.
- No TURN provider or networking jargon appears in patient or staff UI.
