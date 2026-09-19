# Digital Crown — Patient Companion — Canonical Resume

Last verified update: 2026-09-19 — PC-01 visual certification batch
Active lot: REMOTE TRANSPORT GATE — E2E opaque relay

## Product doctrine

Digital Crown cabinet is the clinical source of truth.
Patient Companion is a local-first encrypted patient wallet:
cabinet → one-time QR/manual bridge → encrypted vault on patient phone.

No Firebase/SaaS plaintext clinical data plane.
WhatsApp is not the canonical clinical transport. It may later be an optional notification/deep-link channel with no clinical payload.

## PC-00 — Shell & Local Pairing

PR: #634
Branch: feature/patient-companion-pc00
Current branch HEAD after latest harness correction: 226b5e74f3417b1f77e542672b0f81d3434747e4

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
Latest PC-01 code/test HEAD before docs checkpoint: b25a6bb95b78566e4de481650192d1bce9ec5ecc

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

PC-00:
- exact-head ad6d8ee41981fef3818ba9d9576092427dce9370 had CI/T2/P7/UX1-C/Agenda/DB/Portability/Settings gates green;
- dedicated visual run 35468621741 failed during pairing with `Appairage non validé / Load failed`;
- page/context route interception did not solve the harness failure;
- latest harness now stubs Patient Companion fetch calls inside the browser runtime, independent of API host/port matching;
- latest PC-00 HEAD: 226b5e74f3417b1f77e542672b0f81d3434747e4;
- later visual run 35469896539 proved pairing now reaches the home screen; the remaining failure was the exact dev-harness error `TypeError: Importing a module script failed.`;
- PC-00 harness now ignores only that exact Vite module-noise signature (and known dev-sw CORS noise) after the expected UI is reached;
- latest PC-00 code/test HEAD: 07d97d46f1fd573232205fc42c6c9afc941db63a;
- no visual PASS claimed yet.

PC-01:
- exact-head 2cb97c5763e439c8d3b32fd3dbcc3793324cefb7 had CI/T2/P7/Agenda green;
- dedicated visual run 35468624843 failed from harness code: `ReferenceError: target is not defined`;
- latest harness now uses browser-runtime fetch stubs plus explicit offline-reload API-call counting;
- patient-facing wallet contract hardened: appointments no longer expose internal numeric appointment IDs; shares no longer expose internal numeric resource IDs; opaque `access_id/share_id` remain;
- frontend wallet schema/tests/certification fixtures were aligned and a static backend contract test locks the rule;
- latest PC-01 code/test HEAD: b25a6bb95b78566e4de481650192d1bce9ec5ecc;
- no visual PASS claimed yet.

No Vercel deployment.

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


## PC-00 certification checkpoint — 2026-09-19

PC-00 product/test candidate `3cfceca5601c7562cb30992ee571d8b736f12ffc` is certified by:
- visual `35471266296` SUCCESS;
- CI `35471266310` SUCCESS;
- T2/P7/UX1-C/Button Matrix SUCCESS;
- artifact `10592874065`, digest `sha256:e4f0ff1e392e8a598011ff19afcd8075e1943a28aaf14dedc91f8d6be918da19`;
- 16 Chromium/WebKit BEFORE/AFTER captures manually inspected;
- encrypted vault probes passed;
- visual scope score 8.7/10.

PC-00 documentation closeout was then committed on its branch; latest PC-00 docs HEAD is `c6a84743aee65a6e68437b254d75c6919567080d`. Its docs-only exact-head workflows are currently running and must be green before merge.

PC-01 exact-head `a463ee89fc04bc6172a33626f7dd580068be5576` already has Visual `35470229496`, CI, T2, P7 and Agenda SUCCESS, but it must be reconciled onto the merged PC-00 base before final certification/merge.

No Vercel deployment.


## Remote transport gate B — 2026-09-19

Option B approved. PR #638 on `feature/patient-companion-e2e-relay-gate` defines threat model, JOSE sign-then-encrypt protocol, opaque mailbox capabilities, isolated relay package and negative tests. Base master includes merged PC-00/PC-01. No deployment. Exact-head CI/adversarial certification pending before PC-02.
