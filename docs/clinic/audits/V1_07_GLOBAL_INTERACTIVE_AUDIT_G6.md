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


## Behavioral proof

1. `frontend/src/features/superadmin/SuperAdminDashboard.packButtons.test.tsx`
   - current-code proof for GOLD/PREMIUM/ELITE plan changes;
   - exact 409 downgrade reason;
   - archived/suspended mutation locks;
   - licence extension actions;
   - internal notes;
   - licence history;
   - WhatsApp renewal transport truth;
   - suspend/archive confirmations.

2. `frontend/src/features/superadmin/SuperAdminDashboard.g6TrialCodes.test.tsx`
   - create trial code with exact payload;
   - clipboard only after backend ACK;
   - create refusal has no false success;
   - copy existing activation link + clipboard failure;
   - revoke unused code + server reload;
   - precise revoke refusal;
   - explicit refresh.

## Current-source reconciliation

`handleGrantLicense(..., 'revoke')` exists as an internal handler branch but no current desktop control invokes that action. It is therefore not counted as an exposed button in the G6 interactive denominator.

## Open defect

`LicenseStatusPage.tsx` hardcodes “Votre licence Elite a expiré” for every expired account. `AppUser` exposes no subscription-plan field, so the UI cannot truthfully name a plan here. This remains an open product-truth defect requiring UI BEFORE/AFTER protocol before visible copy remediation.

G6 is not certified while this defect and exact-head CI remain open.
