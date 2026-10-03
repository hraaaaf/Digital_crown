# V1.5-03.2 — Station Identity & Pairing Contract

## Goal
Give each Digital Crown Station a stable server-side identity, a human-editable name, tenant binding, pairing lifecycle and revocation without changing the technical workstation identifier when the display name changes.

## Invariants
1. `workstationId` is immutable and opaque.
2. `displayName` is human-editable, 1–80 chars after trim, tenant-scoped and never used as an authorization key.
3. A Station can be renamed without rotating its workstation token or changing `workstationId`.
4. Pairing codes are short-lived, single-use, HMAC-SHA256 protected with a dedicated configurable pepper, and stored only as hashes server-side.
5. At most one unused pairing code may be active per cabinet; issuing a new code invalidates every older unused code. The invariant is DB-enforced under concurrent issuance.
6. Pairing an additional or untrusted Station requires an authenticated user in the target tenant plus a valid unexpired pairing code. The existing first-owner-workstation bootstrap path remains unchanged.
7. Pairing code generation, rename and revocation require admin authority; privileged mutations require the owner PIN where configured.
8. Pairing-code consumption, workstation creation and the critical pairing audits form one atomic transaction; failure rolls the entire pairing back.
9. Pairing claims are protected by a persistent tenant-wide 5-failures/10-minute DB throttle, independent of worker-local memory, plus the existing failure limiter as defense in depth.
10. Revocation is fail-closed: a revoked workstation identity can no longer authorize protected cabinet access.
11. Station registry never exposes token hashes or pairing-code hashes.
12. Multiple Stations may coexist in the same cabinet.
13. `lastSeenAt` is diagnostic only ("vu récemment"), never a security proof or guaranteed realtime-presence signal.
14. Every pairing, rename and revocation is audited without logging secrets.

## UX
- The current Station name is visible in workstation settings.
- Admin can rename a Station later (examples: `Accueil 1`, `Borne entrée`, `Tablette secrétariat`).
- Registry shows name, mode, status and technical short ID.
- A newly generated pairing code clearly shows its expiry and single-use nature.

## Explicit non-goals
- Patient identity / QR-NFC patient handoff (03.3).
- Appointment arrival bridge (03.4).
- Queue ordering or Wall Display (03.5+).
