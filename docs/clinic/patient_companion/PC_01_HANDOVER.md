# HANDOVER — Digital Crown Patient Companion — PC-01

Updated: 2026-09-19

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
PC-00 current HEAD: 0495ebba61d7b0089159e064d2951942b9951f6f
PC-00 PR: #634

PC-01 branch: feature/patient-companion-pc01
PC-01 PR: #636 draft, base feature/patient-companion-pc00
PC-01 implementation HEAD before this handover update: 9b24efbce62266cec2e6738d30d0eb89b8e9d156

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

PC-01 dedicated visual/runtime certification has not yet been created/run.
PC-00 latest corrective exact-head must still be inspected and closed.

## Remaining

1. create PC-01 matched BEFORE/AFTER workflow:
   - BEFORE = PC-00 candidate
   - AFTER = PC-01
   - 360×800 and 390×844
   - Chromium + WebKit
2. deterministic sync payload then reload with network unavailable;
3. inspect IndexedDB envelope remains ciphertext after PC-01 snapshot;
4. visual comparison + score;
5. PC-01 adversarial review;
6. inspect/close PC-00 #634 exact-head;
7. merge PC-00 only if all gates proven;
8. reconcile PC-01 onto final PC-00;
9. exact-head PC-01 certification;
10. merge PC-01;
11. update canonical + Notion + handover;
12. stop at Remote Transport Gate before PC-02.

## Real blocker

No blocker for PC-01 implementation/certification work.
Merge dependency only: PC-01 cannot merge before PC-00.

## Next exact

Create the dedicated PC-01 BEFORE/AFTER + offline-reload certification workflow and execute it.

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
