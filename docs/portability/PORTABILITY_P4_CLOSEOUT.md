# Portability P4 — Licence & local secrets cross-platform — CLOSEOUT

Status: **CLOSED / VERIFIED**

## Goal
Allow a cabinet to migrate between supported machines/OSes without transporting or trusting the source machine's licence vault, local secrets, sessions or mobile credentials.

## Success verified
- destination-local `.env`, `SECRET_KEY`, `CABINET_MASTER_KEY_HEX` and `backup.key` remain destination-owned;
- `license_vault.bin` is excluded from portable cabinet bundles and is rebuilt/revalidated locally;
- offline licence grace remains strict at 72 hours with clock-rollback protection;
- Firebase unavailability remains non-destructive: `validate_license_with_expiry()` reports `active=None` rather than inventing an inactive licence;
- `/recheck-license` resolves the authenticated `CabinetConfig` identity rather than trusting environment `CLINIC_ID`, and preserves local state when Firebase is unavailable;
- portable restore is detected from validated manifest content, not from the archive filename extension;
- portable rebind invalidates local licence state plus mobile pairings/tokens, then requires destination revalidation;
- SQLAlchemy pools are disposed before restore and on failure/finally paths;
- local licence vault rejects absent/weak/predictable master material and writes atomically with private POSIX permissions through the platform abstraction;
- Guided Restore remains rollback-safe;
- P1 platform-boundary guard remains satisfied on Windows, macOS and Ubuntu.

## Exact proof
- candidate HEAD: `3bc7426848d544183f235244ae8eab7b255d1341`;
- PR `#224` — merged;
- product merge on master: `40cb22d6dddcbae6dee7340dc23956decaf701d8`;
- Portability Runtime Certification `32610745183` — SUCCESS;
- Settings Guided Restore AFTER `32610745196` — SUCCESS;
- Onboarding Settings P2 Visual Certification `32610745220` — SUCCESS;
- T2 Runtime Browser Certification `32610745188` — SUCCESS;
- Catalog Connected Truth Certification `32610745249` — SUCCESS;
- Patient P7 Final Certification `32610745225` — SUCCESS;
- CI `32610745134` — SUCCESS.

## Scope note
P4 changes no product UI. No visual BEFORE/mockup/AFTER gate is applicable to this lot.

## Progress
Closed lots: P0, P1, P2, P3, P4.

Previously credited: `44 EP`.
P4 credit: `8 EP`.
Credited effort: `52 EP` out of `162 EP` = **32.1%**.

No partial EP are credited for an open lot.

## Next exact
P5 — Native/scientific dependency parity: establish a reproducible Windows/macOS Apple Silicon runtime and packaging evidence chain, including controlled model provenance and real non-PHI inference fixtures before any scientific parity claim.
