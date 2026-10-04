# V1.5-03.4 — Station arrival / today's appointment bridge contract

## Goal
After V1.5-03.3 securely identifies an existing patient on a registered Station, resolve only that patient's appointments for the cabinet-local current day and allow an explicit arrival confirmation without introducing autonomous queue logic.

## Existing-state audit — master@c86ba39bdf27e99735f9dbe85fdf70fc48155488
- Canonical appointment persistence is `backend.models.Appointment` in table `appointments`.
- Tenant ownership is `employer_id`; patient linkage is `patient_id`; soft-deleted rows use `deleted_at`.
- Existing appointment status enum has no `ARRIVED` member.
- Existing arrival-equivalent state is `AppointmentStatus.EN_SALLE_ATTENTE` with serialized value `EN_S_ATTENTE`.
- Existing APIs include cabinet/agenda appointment listing, generic appointment update, and patient appointment history, but they require normal authenticated application context and are not a Station-specific patient-session bridge.
- V1.5-03.3 Station sessions already bind an identified patient to one tenant + one registered workstation without exposing patient credentials to the Station.
- `ticket_number` exists on appointments but 03.4 must not populate, compute, reorder, prioritize, or otherwise interpret it.

## Contract
1. The Station may resolve today's appointments only after the 03.3 session is identified, unexpired, unpurged, tenant-bound, and bound to the exact registered Station.
2. "Today" uses the same naive cabinet-local calendar-day representation already used by the agenda database.
3. Resolution is restricted to the session's `patient_id`, same `employer_id`, non-deleted appointments, and Station-relevant states only: `PREVU`, `CONFIRME`, or already-arrived `EN_SALLE_ATTENTE`.
4. Zero matches returns `none` and sets `staffActionRequired=true`. The Station instructs the patient to alert reception and must not create an appointment. This lot does not claim an active staff push/notification channel unless one is separately proven canonical.
5. One match returns `single` and the Station proposes it directly.
6. More than one match returns `multiple`; the patient explicitly chooses one.
7. The Station response is minimal: appointment identifier, start time, duration, scheduling type, and current status. It must not expose another patient's data or clinical notes.
8. Arrival confirmation is explicit and appointment-specific.
9. Station-level semantic `ARRIVED` maps to the existing canonical persisted status `EN_SALLE_ATTENTE`. No duplicate appointment status or database migration is introduced in 03.4.
10. Arrival is idempotent when the appointment is already `EN_SALLE_ATTENTE`.
11. Arrival is allowed only from `PREVU` or `CONFIRME`. Pending request/confirmation, refused, expired, absent, cancelled, in-chair, completed, or other states fail closed.
12. The appointment must still belong to the identified patient, same tenant, same local day, and be non-deleted at the moment of confirmation.
13. Confirmation writes an audit event. It does not assign a ticket number or queue position.
14. 03.4 contains no autonomous queue behavior: no ordering, priority, ticket generation, waiting-time estimation, or passage decision. Those remain V1.5-08 Queue Core.
15. New-patient pre-registration is not activated in 03.4 because no canonical Station new-patient minimal-registration contract exists at this HEAD. A new/unidentified patient is escalated to staff; no patient or appointment is auto-created.
16. Session expiry/purge after identification invalidates both lookup and arrival confirmation.
17. All Station responses remain `Cache-Control: no-store`.

## Required baseline tests
- identified session + zero appointments -> `none`, no writes;
- one appointment today -> `single`;
- multiple appointments today -> `multiple`, stable chronological order;
- yesterday/tomorrow, another patient, another tenant, and soft-deleted appointments are excluded;
- unclaimed, expired, purged, wrong-workstation sessions fail closed;
- arrival updates exactly the selected patient's appointment to `EN_SALLE_ATTENTE`;
- already-arrived confirmation is idempotent;
- cancelled/completed/pending/refused/etc. states cannot be silently converted to arrived;
- cross-patient/cross-tenant appointment ID cannot be marked arrived;
- no `ticket_number` mutation occurs;
- audit evidence is written without patient credentials;
- frontend single/multiple/none flows and explicit confirmation are covered;
- 03.3 identification behavior remains non-regressed.


## Staff assistance signal for zero appointments

When the identified station session resolves to zero eligible appointments, the station explicitly requests staff assistance. The request is persisted in `AuditLog` as `STATION_STAFF_ASSISTANCE_REQUESTED`, scoped to the cabinet and station session, and is idempotent for that session. It contains no patient identity or clinical data.

Authenticated staff with agenda access sees unresolved station assistance on the dashboard. The dashboard refreshes the assistance feed periodically and staff can acknowledge a request. Acknowledgement is persisted separately as `STATION_STAFF_ASSISTANCE_ACKNOWLEDGED`; the original audit event is immutable.

The signal is assistance-only. It MUST NOT create an appointment or patient, assign a ticket, rank, priority, queue position, or estimated waiting time.
