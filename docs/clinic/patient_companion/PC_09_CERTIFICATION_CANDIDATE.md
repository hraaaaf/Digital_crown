# PC-09 — Teleconsultation — Certification Candidate

Status: APP CANDIDATE READY — EXACT-HEAD EVIDENCE IN PROGRESS
Date: 2026-09-23
PR: #689
Branch: `feature/patient-companion-pc09-teleconsultation`

## Goal
Provide a privacy-preserving patient↔cabinet teleconsultation flow with exact identity binding, explicit camera/microphone permission, WebRTC media, and truthful call state.

## Locked architecture
- cabinet DB is canonical for session lifecycle;
- Patient Companion access/tenant/patient binding is reused;
- media never uses the Patient Companion command relay;
- browser WebRTC carries audio/video;
- Patient Companion signed/encrypted operations carry session/signaling control only;
- no recording;
- provider-agnostic coturn-compatible short-lived TURN credentials supported, with server-side shared secret;
- no Vercel deployment.

## Product truth
CONNECTED is not inferred from:
- a session existing;
- offer/answer exchange;
- signaling receipt;
- camera permission;
- local preview.

CONNECTED requires:
1. patient browser RTCPeerConnection state `connected`;
2. staff browser RTCPeerConnection state `connected`;
3. both reports bound to the same canonical session.

## Evidence already implemented
- PC-09 session + signal schema and Alembic migration;
- exact access/tenant/patient scoping;
- session expiry and terminal-state handling;
- access revocation gate;
- signal idempotency/conflict handling;
- bounded signal payload + bounded sync batches;
- real JOSE envelope-size test;
- signaling purge on end/expiry;
- explicit patient acceptance + decline before camera/microphone permission;
- session starts `CREATED`; staff join is not claimed until media setup reaches the join action;
- patient + staff WebRTC UI;
- no MediaRecorder path;
- local tracks stopped and peer connection closed;
- canonical `FAILED` persisted from real peer failure;
- fail-closed media cleanup when session-control sync is lost;
- deterministic frontend truth contract;
- runtime visual harness prepared.

## Visual baseline
BEFORE:
- PC-08 certified runtime run `35859746972`;
- artifact `10750431243`;
- digest `sha256:9181923334458fe680cd8c93beac24d08f2e0c724ea2ea6a0264727b913b287a`.

AFTER target:
- Patient Chromium 360×800;
- Patient Chromium 390×844;
- Patient WebKit 390×844;
- Staff 390×844;
- Staff 768×1024;
- Staff 1280×900.

Visual runtime deliberately captures idle/available-to-join states and does not fake a network-connected media call.

## Exact-head checks required
Pending on final candidate HEAD:
- PC-09 Teleconsultation Certification;
- PostgreSQL Alembic Schema Certification;
- CI;
- PC-09 Runtime AFTER Visual Evidence.

No green status is claimed until exact run results are recorded here.

## Adversarial gates

### Remote signaling
The existing Patient Companion relay is command/ACK and has not been certified for real-time signaling latency/recovery.

### TURN
The candidate can now consume a controlled TURN service using short-lived server-generated credentials without exposing the shared secret.

No controlled TURN service is actually deployed/configured yet.

Therefore the current candidate must still not be described as reliable arbitrary off-network teleconsultation until forced-relay remote E2E passes.

## Full remote-production gate
Before claiming full remote teleconsultation:
- select/control TURN infrastructure;
- issue short-lived TURN credentials;
- measure signaling latency;
- test patient and cabinet on distinct networks;
- force TURN relay and prove media;
- test disconnect/reconnect;
- test permission denial/retry;
- prove CONNECTED truth under real media conditions.

## Human visual gate
Required before merge.

No Vercel deployment.
