# Onboarding ↔ Réglages — P4 Backend / Persistence / Permissions

Status: **CLOSED — implementation complete; final project closure is tracked in `ONBOARDING_SETTINGS_CLOSEOUT.md`.**

## Goal

Make Settings and onboarding persist the canonical P1 ownership model truthfully and atomically.

## Delivered

- authenticated setup owner binding; no global owner lookup;
- backend `settings` permission on Settings mutations;
- `/clinics/me` read without implicit creation;
- strict schema payloads, IF alias round-trip, custom specialty persistence;
- truthful offline mutation failure, no synthetic persisted success;
- `User.nom_complet_ar` and `User.inpe_professionnel`;
- `CabinetConfig.inpe_etablissement`;
- legacy ambiguous `CabinetConfig.inpe` never auto-classified;
- atomic Settings facade: one transaction for practitioner + organization;
- subaccount may edit organization only when permitted and may not mutate principal practitioner identity;
- onboarding two-phase persistence: draft → optional uploads → `complete-setup`;
- only `complete-setup` sets `is_initialized=true`;
- existing-install identity migration is startup-wired and idempotent;
- legacy value migration is conservative and conflict-aware.

## Key evidence

- P4B CI #1615 `32564584627` — SUCCESS.
- P4C CI #1616 `32565251024` — SUCCESS.
- Settings UI CI #1617 `32565754510` — SUCCESS.
- Settings Profile AFTER `32565754488` — SUCCESS, 12/12 captures at 1440/768/390.
- P2 two-phase/setup contracts are repeatedly green in P0/P2/T2 exact-head certification.
- Resync CI #1626 `32572940012` — SUCCESS, proving migration/startup compatibility after master resync.

No Vercel deployment was performed.
