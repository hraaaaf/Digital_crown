# Digital Crown — Patient Companion — Canonical Resume

Last verified update: 2026-09-21 — PC-07 merged; post-merge verification in progress
Active lot: PC-07 — Emergency Photo — post-merge closeout

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

1. certify final docs-inclusive Remote Transport Gate HEAD;
2. mark PR #638 ready and merge only if exact-head gates are green;
3. verify post-merge master;
4. start PC-02 Self-Service Agenda.

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


## Remote transport gate B — current state

Option B approved. PR #638 on `feature/patient-companion-e2e-relay-gate`.

Implemented:
- opaque relay isolated from cabinet backend/data stores;
- ES256 JWS -> ECDH-ES+A256KW/A256GCM JWE;
- `jwcrypto==1.6.1` + browser `jose==6.2.12`;
- patient non-extractable WebCrypto private keys;
- cabinet Windows current-user DPAPI private-key protection;
- atomic key enrollment during one-time local pairing;
- persistent keysets + replay/idempotency receipts;
- 15-minute command TTL + future-clock-skew rejection;
- allow-listed cabinet worker with transactional rollback and encrypted ACK;
- access revocation also revokes the active remote keyset;
- dedicated Python/JS JOSE interoperability + Windows DPAPI certification workflow.

Old exact-head `6dd85ae...` failures were diagnosed as:
- focused Linux workflow missing email-validator;
- Windows DPAPI job accidentally loading full backend pytest conftest;
- frontend TypeScript JsonWebKey metadata typing;
- stale Alembic runtime head.

Those causes are remediated. Additional hardening before final freeze:
- concurrent first-pair cabinet key creation is guarded by the DB unique index plus savepoint/reuse;
- remote ACK operation is the fixed bounded value `command.result`, with the original request operation retained inside the encrypted payload;
- stale competing remote-key route/test artifacts were removed;
- access revocation now revokes the active remote keyset.

Code/test exact-head `6843f4ccd0ca40afe372a96ba7bfee92598ef098` is certified: dedicated Remote Transport Gate `35504753520` SUCCESS, CI `35504753506` SUCCESS, PostgreSQL/Alembic `35504753494` SUCCESS, and all other triggered regressions SUCCESS. This documentation closeout creates a newer docs-only SHA which remains subject to exact-head certification before merge. No merge and no deployment are claimed.

Canonical closeout sequence:
exact-head Remote Transport + CI + Alembic + triggered regression gates -> adversarial VERIFIED -> Notion/handover -> ready/merge #638 -> post-merge -> PC-02.


## Frozen certification candidate — 2026-09-20

Code/test/docs candidate before exact-head certification:
`ca30bd599ed9a74a3c5f4130a1d1ad3c2343c755`

This canonical update supersedes that SHA as the final docs-inclusive candidate. Read the branch HEAD after this commit and use only that exact SHA for final certification evidence.


## Remote Transport Gate B — closeout candidate — 2026-09-20

Verified code/test SHA: `6843f4ccd0ca40afe372a96ba7bfee92598ef098`.

Evidence:
- Remote Transport Gate `35504753520` — SUCCESS.
- Linux job `106062570707` — SUCCESS: relay certification, Python→JavaScript JOSE, JavaScript verification/emission, JavaScript→Python JOSE.
- Windows DPAPI job `106062570833` — SUCCESS.
- CI `35504753506` — SUCCESS.
- PostgreSQL/Alembic `35504753494` — SUCCESS.
- all other triggered non-skipped regression gates — SUCCESS.

The current branch HEAD after this docs-only closeout supersedes the code/test SHA as the merge candidate and requires exact-head certification before PR #638 may merge.

No deployment performed.


## PC-06 closeout / PC-07 start — 2026-09-21

PC-06 Patient Finance:
- PR #645 merged;
- merge commit `b4e40fa1f3a63d4d7bf4d91223fa376902dcd7a2`;
- pre-merge exact-head `84ec5d62af4778f00ffc34d25d174d8bcd2e98b2` had PC-06 Certification, BEFORE, AFTER, CI, T2, P7 and Remote Transport SUCCESS;
- exact-head AFTER artifact `10628894211`, digest `sha256:42d4791dae424527fab95192ba50eca703debcce769feef8913e363d6519583d`;
- post-merge no workflow was auto-triggered on the squash commit, so content identity was checked directly: all 18 PR-modified files have identical blob SHAs between certified HEAD and merged master;
- no Vercel deployment.

PC-07:
- canonical roadmap target: Emergency Photo;
- branch: `feature/patient-companion-pc07-emergency-photo`;
- audit-before-code gate created;
- exact behavior is intentionally not invented before inspection of existing media/photo/storage and remote-transport primitives.

Next exact:
1. audit current media/photo/storage/upload primitives;
2. determine remote transport compatibility for patient-originated media;
3. create `PC_07_EMERGENCY_PHOTO_ARCHITECTURE_MAP.md`;
4. lock exact Goal / Success / Proof;
5. only then implement.


## PC-07 merged / post-merge closeout — 2026-09-21

PC-07 Emergency Photo:
- PR #648 merged;
- certified pre-merge product HEAD: `974c364178302cca697dfdfc5a15f85626f19f23`;
- merge commit: `f4576d5127799b66eae891afb82ebd439d8b48d0`;
- PC-07 Certification `35588652802` SUCCESS;
- Remote Transport `35588652799` SUCCESS;
- Alembic `35588652849` SUCCESS;
- BEFORE `35588652855` SUCCESS;
- AFTER `35588652761` SUCCESS;
- CI `35588652925` SUCCESS;
- human visual approval received before merge;
- conservative visual score: 9.2/10;
- no Vercel deployment.

Post-merge at this checkpoint:
- master is exactly `f4576d5127799b66eae891afb82ebd439d8b48d0`;
- Cabinet Upgrade PostgreSQL Certification `35589112147` queued;
- CI `35589112155` queued;
- PC-07 is not declared fully closed until merge-commit checks are green.

Next exact:
1. verify merge-commit post-merge workflows;
2. if green, mark PC-07 post-merge verified;
3. switch active lot to PC-08 — Secure Messaging;
4. prepare PC-08 start handover; no Vercel deployment.
