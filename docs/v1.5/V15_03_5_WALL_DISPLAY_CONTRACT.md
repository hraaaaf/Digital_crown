# V1.5-03.5 — Wall Display + staff patient call contract

## Goal

Add a public waiting-room wall surface distinct from the Station kiosk and allow an authenticated agenda staff member to call a waiting patient without introducing the autonomous Queue Core reserved for V1.5-08.

## Existing-state boundary

- AppointmentStatus.EN_SALLE_ATTENTE remains the canonical arrival/waiting status.
- Appointment.ticket_number already exists and may already be populated by legacy/staff workflows.
- V1.5-03.4 intentionally did not generate or interpret ticket numbers.
- V1.5-08 owns autonomous queue ordering, priorities, wait-time logic and the future CALLED queue state.
- V1.5-09 will integrate Digital Crown / Pocket / Station / Wall with that common Queue Core.

## 03.5 contract

1. /station/wall is a separate public-facing render from /station; it reuses the registered Station workstation boundary rather than creating a fourth workstation authority.
2. The public feed exposes only ticketNumber, pseudonymous initials, bounded current-call metadata (callId, expiresAt), and aggregate waiting count.
3. The public feed never exposes full patient name, patient ID, appointment ID, phone, motif, notes, diagnosis or other clinical data.
4. Only today's non-deleted EN_SALLE_ATTENTE appointments belong to the wall source.
5. An appointment without a persisted ticket is counted but omitted from public identifiers until staff explicitly supplies a 1–999 ticket during the call action.
6. Ticket assignment in 03.5 is explicit staff input only. There is no automatic numbering, ranking, priority, reordering, estimated wait or passage decision.
7. Same-day active waiting tickets must be unique per tenant at call time. SQLite uses BEGIN IMMEDIATE; PostgreSQL uses a tenant-scoped transaction advisory lock to serialize explicit assignment.
8. Staff call is allowed only for an authenticated user with agenda permission, same tenant, same local day, non-deleted, currently EN_SALLE_ATTENTE.
9. Staff call writes STATION_WALL_PATIENT_CALLED in AuditLog; the audit details contain the display ticket and TTL, never patient identity.
10. Calling does not change the appointment status to EN_FAUTEUIL and does not create a CALLED appointment state.
11. One call remains active for 20 seconds. A repeat call creates a new event and therefore a new bounded call window.
12. Multiple registered Station screens polling the same tenant endpoint observe the same persisted latest active call.
13. Visual call is authoritative. Optional sound is user-enabled locally and limited to one short chime per new call ID; audio failure never changes workflow state.
14. Feed failure renders an explicit unavailable state rather than assuming an empty waiting room.
15. All wall endpoints are Cache-Control: no-store.

## Visual target

Public wall target: calm clinical hierarchy, large distance-readable ticket, initials secondary, no patient photo, no clinical metadata, no navigation chrome, no queue-management controls. Waiting state uses compact pseudonymous cards; calling state replaces the waiting grid with a dominant call card. Required proof viewports: 390, 430, 768, 1280 px.

The existing Station kiosk is the relevant BEFORE/reference because no wall surface existed before 03.5. Kiosk source files must remain byte-identical to master in this lot; the AFTER wall must be visibly and structurally distinct.

## Required proof

- backend tenant/status/day/ticket/call/privacy tests;
- explicit no-full-name/no-clinical-data response assertions;
- call expiry proof;
- duplicate-ticket rejection;
- Station 03.1–03.4 targeted regression;
- staff-control frontend tests;
- wall waiting/calling/unavailable frontend tests;
- frontend build;
- kiosk-baseline identity check;
- BEFORE reference + AFTER waiting/calling captures at 390/430/768/1280;
- two adversarial reviews on the same exact HEAD, then a confirmation pass;
- exact-head CI collection/execution/skips audit;
- explicit human validation of AFTER captures before visual closeout.