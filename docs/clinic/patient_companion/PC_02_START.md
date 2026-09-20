# PC-02 — Self-Service Agenda — Start Contract

Status: COMPLETE — certified exact-head before closeout commit
Base: master@`ae4f820aad6ea934c3b430d3c8ccf81da73648ba`
Branch: `feature/patient-companion-pc02-self-service-agenda`

## Goal

Allow a paired patient to request, reschedule, or cancel an appointment remotely without bypassing the cabinet agenda authority.

## Success

1. Only cabinet-authorized appointment choices are exposed to Patient Companion.
2. Patient commands travel through the certified Remote Transport Gate B.
3. The cabinet revalidates availability/conflicts at mutation time.
4. Create/reschedule/cancel are idempotent through the existing remote receipt ledger.
5. The phone never labels an offline/queued request as confirmed.
6. No internal numeric patient, appointment, practitioner, or resource IDs are exposed in the patient command contract.
7. Staff agenda behavior remains unchanged.

## Existing verified foundations

- Gate B merged as PR #638; merge commit `ae4f820aad6ea934c3b430d3c8ccf81da73648ba`.
- Existing agenda mutations already enforce tenant scoping, practitioner validation, working-hours availability, appointment overlap checks and resource conflicts.
- Remote worker already enforces decrypt/verify, freshness, replay/idempotency, allow-listed handlers and transactional ACK.

## Implementation boundary

PC-02 must reuse the existing agenda invariants rather than create a second scheduling engine.

Patient-facing operations:
- `agenda.create`
- `agenda.reschedule`
- `agenda.cancel`

Patient-facing references must be opaque UUIDs. Mapping to internal agenda rows remains cabinet-side.

A remote command result is only:
- ACCEPTED after cabinet transaction commits; or
- REJECTED with a stable non-sensitive code.

Queued/pending locally is not confirmation.

## First implementation slice

1. Extract/reuse cabinet agenda mutation-domain functions behind the staff router.
2. Add opaque patient appointment reference persistence/mapping.
3. Add three allow-listed PC-02 remote handlers.
4. Add patient-side encrypted command queue/state machine.
5. Add mobile UI only after the domain contract/tests are locked.

## UI gate

Before visual implementation:
BEFORE capture -> written target/mockup -> implementation -> AFTER same viewports -> visual comparison/tests.

## Non-goals

- no relay deployment in this lot;
- no Vercel deployment;
- no new cloud clinical database;
- no WhatsApp clinical transport;
- no optimistic “confirmed” state before cabinet ACK.


## Closeout

Functional candidate certified at `a1c0e1bc8d317e7d2086ff3ae3d0806efcb770f8`.
Canonical closeout evidence: `docs/clinic/patient_companion/PC_02_CLOSEOUT.md`.

The final documentation-only closeout commit must itself receive a fresh exact-head CI cycle before merge.
