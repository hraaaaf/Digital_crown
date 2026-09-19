# Digital Crown V1-07 — Global Interactive Audit — G6

Status: IN PROGRESS

## Goal
Certify commercial administration, SuperAdmin client lifecycle, packs, licences, trial activation codes and licence-status controls.

## Success
- SuperAdmin read/mutation controls have behavioral proof;
- GOLD / PREMIUM / ELITE plan changes and downgrade refusal are proved;
- licence grants/revocation, notes, history, renewal transport, suspend/archive are proved;
- trial-code create/copy/revoke/refusal paths are proved;
- licence-status actions are proved without false product claims;
- exact-head frontend tests + build pass.

## Reusable current-code proof
`frontend/src/features/superadmin/SuperAdminDashboard.packButtons.test.tsx`
currently proves:
- GOLD/PREMIUM/ELITE plan changes;
- precise 409 downgrade refusal;
- immutable archived/suspended states;
- licence duration actions;
- notes;
- licence history;
- WhatsApp renewal feedback;
- suspend/archive confirmation and mutation.

Prior V1-07 LOT1/LOT3/#629 evidence remains reusable only where current source is unchanged.

## Newly identified gap
`frontend/src/pages/LicenseStatusPage.tsx` currently displays “Votre licence Elite a expiré” for every expired user while `AppUser` has no subscription-plan field. This is a product-truth defect candidate, not yet remediated because any visible copy change must follow the UI BEFORE/AFTER protocol.

## Certification gate
Do not certify G6 until:
1. trial-code controls are covered;
2. licence-status actions and the hardcoded pack wording are resolved/proved;
3. exact-head frontend tests + build pass;
4. Notion and this canonical file contain final evidence.
