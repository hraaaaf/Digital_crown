# V1.5-03.3 ? Patient identification + QR/NFC session contract

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
8. Creating a new session purges any prior non-purged session for that Station.
9. The Station never receives Patient Companion access tokens.
10. This lot does not mark ARRIVED and does not create/reorder queue state; those belong to 03.4+.
11. No kiosk camera capture is introduced.

## Remaining 03.3 slice
Configured fallback identification (phone + date of birth or name + date of birth), kiosk UX wiring, Patient Companion deep-link claim UX, responsive/200% visual proof and adversarial closeout.
