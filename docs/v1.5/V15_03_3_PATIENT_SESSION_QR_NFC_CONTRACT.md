# V1.5-03.3 — Patient identification + QR/NFC session contract

## Goal
Identify a patient on one registered Station through a short-lived, one-shot handoff without exposing Patient Companion credentials or clinical data to the public kiosk.

## Invariants
1. A session is bound to one tenant and one registered Station.
2. The handoff secret is random, stored only as SHA-256 server-side, expires after 120 seconds and is single-use.
3. QR and NFC carry the same opaque handoff URL; neither contains patient identity or clinical data.
4. Claim requires an already-authenticated Patient Companion identity and an active access belonging to the same tenant.
5. Claim is atomic. Replay or concurrent second claim fails closed.
6. Station status is readable only by the exact registered Station that created the session.
7. Expiry or explicit purge clears patient/access references.
8. Creating a new session purges any prior non-purged session for that Station; the database enforces at most one non-purged session per Station under concurrency.
9. The Station never receives Patient Companion access tokens.
10. A cabinet may configure fallback as phone + birth date, name + birth date, or disabled; fallback is disabled by default until explicitly enabled.
11. Fallback matching is tenant-scoped, requires exactly one active patient match, emits only generic failure responses, and locks Station fallback after five failed attempts within a rolling 15-minute window, including across regenerated sessions.
12. Fallback credentials are never written to audit logs; only the selected mode is recorded on successful identification.
13. Patient Companion deep-link claim requires explicit context selection when several patient contexts exist on the phone.
14. This lot does not mark ARRIVED and does not create/reorder queue state; those belong to 03.4+.
15. No kiosk camera capture is introduced.

## UX
- “J’ai rendez-vous” opens a short Station identity session.
- QR is the primary path; NFC carries the same handoff URL.
- A configured fallback is offered only when enabled by the cabinet.
- Successful identification shows the patient name and explicitly states that arrival has not yet been recorded.
- Back, expiry, replacement session, or timeout purge the Station session references.

## Remaining 03.3 gate
Responsive/200% BEFORE/AFTER evidence, exact-head CI/PostgreSQL certification, two adversarial perspectives to convergence, and one additional clean confirmation pass.
