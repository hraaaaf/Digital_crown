# HANDOVER — Digital Crown Patient Companion — PC-01

Updated: 2026-09-19 — visual certification batch

## Goal

PC-01 — Local Patient Wallet Sync:
server-authorized cabinet resources → same encrypted Patient Companion device vault → useful offline patient wallet.

Success:
- authorized appointments/shares sync;
- encrypted local snapshot;
- offline reload;
- freshness visible;
- failed sync preserves last snapshot;
- session expiry explicit;
- no cloud clinical data plane.

## Verified repository state

Repo: hraaaaf/Digital_crown
PC-00 branch: feature/patient-companion-pc00
PC-00 latest code/test HEAD: 226b5e74f3417b1f77e542672b0f81d3434747e4
PC-00 PR: #634

PC-01 branch: feature/patient-companion-pc01
PC-01 PR: #636 draft, base feature/patient-companion-pc00
PC-01 latest code/test HEAD before docs checkpoint: 81b7468fa9b3ecdd6317f3a306262a57e1379df5

Exact-head runs for 9b24efbc:
- CI 35461919616 SUCCESS
- T2 Runtime Browser Certification 35461919613 SUCCESS
- Agenda A5 Visual Evidence 35461919609 SUCCESS
- M6-I Biometric Passkey SKIPPED expected
- PR Merge Summary SKIPPED because draft/dependency state

## Done in PC-01

- docs/clinic/patient_companion/PC_01_START.md
- encrypted PatientWalletSnapshot schema in PatientCompanionStorage.ts
- PatientCompanionSync.ts
- appointments sync via existing /contexts/{access_id}/appointments
- shares sync via existing /contexts/{access_id}/shares
- atomic snapshot policy: persist only after both fetches succeed
- offline wallet UI
- last-sync timestamp
- offline and expired-session messaging
- session expiry migration
- tests for authorized sync/failure preservation/offline rendering
- docs/ux/PC_01_PATIENT_WALLET_TARGET.md
- canonical resume file: docs/clinic/patient_companion/PATIENT_COMPANION_CANONICAL.md

## Important decisions

1. Patient Companion stays local-first.
2. Cabinet remains clinical source of truth.
3. Patient phone stores an encrypted local wallet.
4. Current device session TTL is 30 days; no indefinite-connectivity claim.
5. WhatsApp is not clinical transport. Future optional notification/deep-link only.
6. Remote transport is a mandatory architecture/security human gate before PC-02.
7. PC-01 may be developed while PC-00 CI is unresolved, but cannot merge before PC-00 final certification/merge and reconciliation.

## In progress

PC-00 dedicated visual:
- exact-head ad6d8ee41981fef3818ba9d9576092427dce9370 had all major non-PC00 visual gates green;
- run 35468621741 failed during pairing with `Load failed`;
- latest browser-runtime fetch harness code HEAD: 226b5e74f3417b1f77e542672b0f81d3434747e4;
- exact-head visual outcome pending.

PC-01 dedicated visual:
- exact-head 2cb97c5763e439c8d3b32fd3dbcc3793324cefb7 had CI/T2/P7/Agenda green;
- run 35468624843 failed from harness code `ReferenceError: target is not defined`;
- latest browser-runtime fetch harness code HEAD: 81b7468fa9b3ecdd6317f3a306262a57e1379df5;
- exact-head visual outcome pending.

No Vercel deployment.

## Remaining

1. inspect PC-01 dedicated visual/CI exact-head results;
2. if red, diagnose and correct immediately;
3. if green, download/inspect BEFORE/AFTER artifact and record visual score;
4. inspect PC-00 corrected exact-head gates;
5. fix any remaining PC-00 red gate;
6. merge PC-00 only after proof is complete;
7. reconcile PC-01 onto final PC-00;
8. rerun final PC-01 exact-head certification;
9. merge PC-01;
10. update canonical + Notion + handover;
11. stop at Remote Transport Gate before PC-02.

## Real blocker

No blocker for PC-01 implementation/certification work.
Merge dependency only: PC-01 cannot merge before PC-00.

## Next exact

Read the new exact-head PC-00 and PC-01 visual results. Red → diagnose/fix immediately. Green → inspect BEFORE/AFTER artifact, encrypted-vault probe and offline-reload proof before certifying.

## Remaining sequence

PC-01 visual/runtime evidence
→ adversarial review
→ PC-00 closeout/fix if needed
→ PC-00 merge/post-merge
→ PC-01 reconcile
→ PC-01 exact-head certification
→ PC-01 merge/post-merge
→ canonical/Notion/handover closeout
→ Remote Transport Gate.

No Vercel deployment authorized.
