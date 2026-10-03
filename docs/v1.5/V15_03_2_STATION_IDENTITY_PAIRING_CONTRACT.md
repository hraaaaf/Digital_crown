# V1.5-03.2 — Station Identity & Pairing Contract

## Goal
Give each Digital Crown Station a stable server-side identity, a human-editable name, tenant binding, pairing lifecycle and revocation without changing the technical workstation identifier when the display name changes.

## Invariants
1. `workstationId` is immutable and opaque.
2. `displayName` is human-editable, 1–80 chars after trim, tenant-scoped and never used as an authorization key.
3. A Station can be renamed without rotating its workstation token or changing `workstationId`.
4. Pairing codes are short-lived, single-use and stored only as hashes server-side.
5. Pairing a new Station requires an authenticated user in the target tenant plus a valid unexpired pairing code.
6. Pairing code generation, rename and revocation require admin authority; privileged mutations require the owner PIN where configured.
7. Revocation is fail-closed: a revoked workstation identity can no longer authorize protected cabinet access.
8. Station registry never exposes token hashes or pairing-code hashes.
9. Multiple Stations may coexist in the same cabinet.
10. Every pairing, rename and revocation is audited without logging secrets.

## UX
- The current Station name is visible in workstation settings.
- Admin can rename a Station later (examples: `Accueil 1`, `Borne entrée`, `Tablette secrétariat`).
- Registry shows name, mode, status and technical short ID.
- A newly generated pairing code clearly shows its expiry and single-use nature.

## Explicit non-goals
- Patient identity / QR-NFC patient handoff (03.3).
- Appointment arrival bridge (03.4).
- Queue ordering or Wall Display (03.5+).
