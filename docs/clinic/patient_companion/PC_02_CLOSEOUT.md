# PC-02 — Self-Service Agenda — Closeout

Status: FUNCTIONALLY CERTIFIED — final documentation exact-head cycle pending
Branch: `feature/patient-companion-pc02-self-service-agenda`
PR: #639
Functional certified HEAD: `a1c0e1bc8d317e7d2086ff3ae3d0806efcb770f8`
Base: `ae4f820aad6ea934c3b430d3c8ccf81da73648ba`
Deployment: none

## Goal

Allow a paired patient to request, reschedule, or cancel an appointment remotely while the cabinet remains authoritative, with opaque references, E2E transport, idempotent mutations, offline-safe local state, and no false confirmed state.

## Verified functional proof

Exact-head `a1c0e1bc8d317e7d2086ff3ae3d0806efcb770f8`:

- Remote Transport Gate: run `35525358951` — SUCCESS
- CI: run `35525358986` — SUCCESS
- Patient P7 Final Certification: run `35525359025` — SUCCESS
- PostgreSQL Alembic Schema Certification: run `35525359023` — SUCCESS
- Portability Runtime Certification: run `35525358987` — SUCCESS
- Portability P5 Native Dependency Certification: run `35525359001` — SUCCESS
- T2 Runtime Browser Certification: run `35525359008` — SUCCESS
- PC-00 Patient Companion Visual Certification: run `35525359055` — SUCCESS
- V1-07 Commercial Pack Button Matrix: run `35525358956` — SUCCESS
- Agenda A5 Visual Evidence: run `35525359011` — SUCCESS
- Settings R11 TemplateBuilder Dependency Audit: run `35525359026` — SUCCESS
- Settings TemplateEngine Reachability Certification: run `35525359235` — SUCCESS

Expected skips:
- M6-I Biometric Passkey Certification: skipped
- PR Merge Summary: skipped while PR remains draft

## BEFORE / AFTER visual proof

Same viewports and engines:
- Chromium 360x800
- Chromium 390x844
- WebKit 360x800
- WebKit 390x844

BEFORE:
- run `35525359116` — SUCCESS
- artifact `pc02-agenda-before`
- artifact id `10609886293`
- digest `sha256:05200a9cd48b74299249afefd58c3f84dbb1761d6267069d2ad0518d0bc95fbc`

AFTER:
- run `35525359010` — SUCCESS
- artifact `pc02-agenda-after`
- artifact id `10610131328`
- digest `sha256:2201eaafd9d99ffefb946da0fdb1c84ffa0bfbd9a46ab5aa45f68c8441c6b92d`

Evidence JSON on both artifacts reports `horizontalOverflow: false` for every viewport.

Manual screenshot inspection confirmed:
- appointment time is the strongest datum;
- confirmed status is explicit and separate from request state;
- create/reschedule/cancel affordances are visible and touch-sized;
- slot selection stays inside the existing mobile flow;
- offline warning explicitly states a request is stored locally and is never shown as confirmed;
- Chromium/WebKit renderings are materially consistent;
- no horizontal clipping or broken layout was observed.

Visual score: **8.8 / 10**.

The score is intentionally not 10/10: the expanded agenda panel creates a long mobile page and the booking card remains visually dense, even though hierarchy, consistency and safety messaging are good.

## Gate B / security boundary

PC-02 reuses the already merged Remote Transport Gate B foundation from PR #638.

Verified in this lot:
- remote command path remains opaque and encrypted;
- cabinet performs the authoritative mutation;
- confirmed state requires verified cabinet ACK;
- remote receipt ledger preserves replay/idempotency semantics;
- pairing and access revocation remain covered;
- remote keyset lookup now resolves the opaque patient context to the internal access row safely;
- no deployment or relay production mutation occurred.

PR #639 itself currently has no review submissions and no review threads. The PC-02 start contract does not define a new independent-review gate beyond the already-certified Gate B foundation.

## Defects found and corrected during certification

- missing `backend.models` import in remote worker audit path;
- remote focused gate import pollution / over-broad backend bootstrap;
- TypeScript UUID and agenda-operation typing mismatches;
- frontend stale agenda assertions;
- TeamManager timing-sensitive mutation tests;
- real runtime bug: `patient_companion_agenda.py` treated `PatientPrincipal` as if it exposed an internal `id`; fixed by resolving `PatientCompanionAccess` using opaque-context fields before keyset lookup.

## Final merge condition

This closeout commit is documentation-only. Before merge, run the normal exact-head workflows once more on the final HEAD and require the critical gates to remain green.

No Vercel deployment is authorized or required for PC-02.
