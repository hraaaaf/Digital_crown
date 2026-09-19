# Digital Crown — Patient Companion — Canonical Resume

Last verified update: 2026-09-19 — PC-01 visual certification batch
Active lot: PC-01 — Local Patient Wallet Sync

## Product doctrine

Digital Crown cabinet is the clinical source of truth.
Patient Companion is a local-first encrypted patient wallet:
cabinet → one-time QR/manual bridge → encrypted vault on patient phone.

No Firebase/SaaS plaintext clinical data plane.
WhatsApp is not the canonical clinical transport. It may later be an optional notification/deep-link channel with no clinical payload.

## PC-00 — Shell & Local Pairing

PR: #634
Branch: feature/patient-companion-pc00
Current verified branch HEAD: 0495ebba61d7b0089159e064d2951942b9951f6f

Implemented:
- /companion patient route outside staff auth;
- one-time QR/manual local bridge;
- device-scoped Patient Companion bearer identity;
- encrypted IndexedDB vault using AES-GCM + non-extractable WebCrypto key;
- local/offline reopen;
- multi-context picker;
- revocation cuts future server access;
- explicit cabinet reachability check;
- insecure non-loopback HTTP pairing refused;
- deep-link secret scrubbed before network request;
- runtime router mounted.

Known session rule:
- current device credential TTL = 30 days;
- do not claim indefinite connectivity;
- PC-01 owns expiry/re-pairing UX; future renewal design must remain secure.

PC-00 certification is not declared complete here until its own exact-head gates/artifacts are closed.

## PC-01 — Local Patient Wallet Sync

PR: #636 (draft)
Branch: feature/patient-companion-pc01
Base branch: feature/patient-companion-pc00
Current verified HEAD before this canonical update: 0dda8f1d11f45c19db32eaf26c4a3381a43722a1

Dependency:
PC-01 development can continue independently, but PC-01 must not merge before PC-00 is certified/merged and PC-01 is reconciled onto the final PC-00 state.

Implemented:
- versioned PatientWalletSnapshot inside the same encrypted vault;
- sync of server-authorized appointments endpoint;
- sync of server-authorized shares endpoint;
- sync writes snapshot only after both reads succeed;
- failed/401 sync does not overwrite last offline snapshot;
- offline rendering of appointments and shared document/media metadata;
- last-sync timestamp;
- cabinet offline state;
- expired session state;
- stored pairing expiry migration;
- explicit manual sync action;
- PC-01 sync unit tests;
- PC-01 offline wallet UI test;
- visual target locked at docs/ux/PC_01_PATIENT_WALLET_TARGET.md.

Verified exact-head CI for PC-01 HEAD 9b24efbc…:
- CI run 35461919616 — SUCCESS
- T2 Runtime Browser Certification 35461919613 — SUCCESS
- Agenda A5 Visual Evidence 35461919609 — SUCCESS
- M6-I Biometric Passkey — SKIPPED expected
- PR Merge Summary — SKIPPED because draft/dependency state

No Vercel deployment.

## Remote transport gate — before PC-02

PC-02+ may initiate actions while patient is outside cabinet LAN.
A human architecture/security gate is mandatory before implementation.

Candidates to evaluate:
1. hardened direct cabinet endpoint via controlled tunnel/domain;
2. end-to-end encrypted opaque relay that cannot read clinical payloads.

Forbidden:
- expose SQLite/media shares directly;
- Firebase/SaaS plaintext clinical database;
- assume LAN reachability remotely;
- silently turn Digital Crown into SaaS.

WhatsApp:
- allowed later only for notification/deep-link;
- no clinical documents/photos/questionnaires/payment/chat payload in WhatsApp;
- not source of truth.

## Roadmap

Wave A:
PC-00 → PC-01

Then:
REMOTE TRANSPORT GATE

Wave B:
PC-02 Self-Service Agenda
PC-03 Medical Questionnaires
PC-04 Consent Vault patient-facing
PC-05 Notifications

Wave C:
PC-06 Finance
PC-07 Emergency Photo
PC-08 Secure Messaging

Wave D:
PC-09 Teleconsultation
PC-10 Satisfaction/Testimonials

## Latest verified passage

PC-01:
- dedicated workflow added: PC-01 Patient Wallet Visual Certification;
- matched BEFORE = live PC-00 PR base, AFTER = PC-01;
- Chromium + WebKit, 360×800 + 390×844;
- runtime proof requires successful sync, encrypted envelope with no appointment/document/token plaintext, then offline reload with zero API requests;
- adversarial review added at docs/clinic/patient_companion/PC_01_ADVERSARIAL_REVIEW.md;
- latest PC-01 implementation carry-forward HEAD before canonical update: 0dda8f1d11f45c19db32eaf26c4a3381a43722a1;
- dedicated PC-01 workflow was queued on prior exact head; latest docs/test commit has not yet shown runs at the verification instant.

PC-00 parallel closeout:
- visual failure diagnosed: visual harness used a non-JWT fake token after expiry decoding was introduced;
- fixed harness with syntactically valid expiring JWT;
- legacy D2 failure diagnosed: test still created legacy email invitation while status intentionally reports canonical local_bridge pending invitation;
- D2 test updated to local-invitation and to assert raw QR token is not returned at all;
- latest PC-00 HEAD: c44a0e293e2aea216fbf3ddc03dac9a3c59a5ec8;
- new exact-head results pending; no PASS claimed.

## Next exact

1. read exact-head PC-01 visual/CI results when available and fix any red gate;
2. inspect PC-01 screenshots/artifact when workflow is green and record visual comparison/score;
3. read exact-head PC-00 corrected gates and close remaining red gates;
4. merge PC-00 only after all required proof is green;
5. reconcile PC-01 onto final PC-00;
6. final exact-head PC-01 certification and merge;
7. update canonical + Notion + handover;
8. stop at Remote Transport Gate before PC-02 unless architecture is explicitly decided.

## Canonical references

- docs/clinic/patient_companion/PC_00_SHELL_ACTIVATION.md
- docs/clinic/patient_companion/PC_00_ADVERSARIAL_REVIEW.md
- docs/clinic/patient_companion/PATIENT_COMPANION_V2_ROADMAP.md
- docs/clinic/patient_companion/PC_01_START.md
- docs/ux/PC_01_PATIENT_WALLET_TARGET.md

## Resume rule

At every significant work passage:
1. verify repo/HEAD/PR/CI;
2. update this canonical file with only verified state;
3. update the Digital Crown Notion page;
4. update PC_01_HANDOVER.md with Goal, verified state, done/in-progress/remaining, decisions, exact refs, blocker, Next exact and remaining sequence.
