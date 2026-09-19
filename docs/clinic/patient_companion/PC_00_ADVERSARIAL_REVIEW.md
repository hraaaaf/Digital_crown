# PC-00 — Adversarial Review

Status: IN PROGRESS — exact-head CI and visual evidence pending.

## Scope

Candidate branch: feature/patient-companion-pc00
Base: master@87543ccd8515dd9cdee94495dbe7001bce22331d

Review target:
- patient pairing boundary;
- patient device identity;
- encrypted local persistence;
- route isolation;
- revocation;
- visual/mobile contract;
- roadmap boundary against accidental cloud/SaaS drift.

## Findings and remediation

### F-01 — Existing Patient Companion code was not runtime-mounted
Severity: blocker

Observed:
backend/routers/patient_companion*.py existed but backend/main.py did not include the router.

Risk:
A repository-level feature inventory could falsely count inaccessible code as a working product feature.

Remediation:
Mount patient_companion.router under /api/patient-companion.

Required proof:
runtime test reaches POST /api/patient-companion/pair and GET /api/patient-companion/me.

Status: remediated in code; CI proof pending.

### F-02 — First PC-00 draft behaved like a Firebase token portal
Severity: blocker / architecture violation

Observed:
first draft UI asked for a raw Firebase ID token.

Risk:
contradicted the approved local-first QR bridge doctrine and created unnecessary cloud/auth coupling.

Remediation:
remove Firebase token UI from canonical Patient Companion flow. Canonical pairing is QR/manual one-shot local bridge. Legacy Firebase activation code remains compatibility-only and is not used by the active patient shell.

Status: remediated; frontend test + visual proof pending exact-head CI.

### F-03 — Patient session must not be plaintext Web Storage
Severity: high

Risk:
localStorage/sessionStorage are easy accidental leak surfaces and are shared with unrelated web auth conventions in the desktop app.

Remediation:
dedicated IndexedDB vault, AES-256-GCM, WebCrypto non-extractable CryptoKey, encrypted state envelope. Patient Companion does not write its token or manual code to localStorage/sessionStorage.

Required proof:
real browser IndexedDB inspection in Chromium and WebKit after pairing.

Status: implemented; visual certification pending.

Limitation:
a non-extractable same-origin CryptoKey is not a claim of hardware-backed or XSS-proof storage. The design protects at-rest state from plaintext persistence/cloud duplication; a future biometric/OS-bound hardening may be evaluated separately.

### F-04 — Deep-link QR secret remained in browser URL during pairing
Severity: high

Risk:
URL could leak through screenshots, history, referrer behavior, support captures, or unrelated browser tooling.

Remediation:
replace /companion?token=... with /companion before issuing the pairing request. The one-time credential remains memory-only.

Required proof:
frontend test asserts search string is empty inside the mocked network call.

Status: implemented; CI proof pending.

### F-05 — GET authentication path mutated identity state
Severity: medium

Observed:
local device identity verification updated last_seen_at and committed during reads.

Risk:
read operations become hidden writes and weaken deterministic/offline/read-only behavior.

Remediation:
token verification is read-only.

Status: remediated.

### F-06 — Staff status mixed local and legacy invitation types
Severity: medium

Risk:
canonical local QR admin UI could surface a legacy Firebase pending invitation as if it were the active local bridge.

Remediation:
pending invitation status filters recipient_type=local_bridge.

Status: remediated.

### F-07 — Patient pairing over insecure LAN transport
Severity: blocker for real patient use

Risk:
the one-time secret and returned device session could be exposed on an unencrypted LAN connection.

Existing platform invariant:
run_real_backend.ps1 refuses non-loopback cabinet binding without TLS cert/key and routes secure mobile runtime through HTTPS.

Additional remediation:
PatientCompanionApp refuses pairing in a non-secure browser context except localhost/127.0.0.1 test/dev loopback.

Status: remediated in code; CI proof pending.

### F-08 — Heavy QR library loaded for every offline wallet opening
Severity: low / performance

Risk:
unnecessary patient bundle and slower offline shell.

Remediation:
dynamic import html5-qrcode only when the scan phase is entered, following the React bundle-defer guidance.

Status: remediated.

### F-09 — Multiple stored contexts silently reused prior active context
Severity: medium / privacy UX

Risk:
a parent/guardian device with several linked patients could reopen the wrong context without an explicit choice.

Remediation:
when >1 contexts exist on startup, force context picker; expose explicit “Changer de dossier”.

Status: remediated; unit test pending CI.

### F-10 — Remote V2 functions could silently reintroduce cloud clinical storage
Severity: architecture blocker before PC-02

Risk:
self-service appointments/chat/payment outside cabinet LAN require transport and could tempt plaintext Firebase/SaaS storage.

Remediation:
canonical roadmap inserts REMOTE TRANSPORT GATE before PC-02. Allowed candidates are direct hardened cabinet endpoint or an E2E encrypted opaque relay. Plaintext clinical SaaS/Firebase is explicitly forbidden.

Status: roadmap locked; future human gate.

## Positive invariants currently present

- no staff JWT issued to Patient Companion;
- opaque access_id used instead of public numeric patient id;
- one-time invitation consumption is atomic;
- access revocation is rechecked server-side on every Patient Companion bearer read;
- cabinet licence remains authoritative for patient device synchronization;
- no PC-01+ feature is shown as active;
- no Vercel deployment authorized or performed.

## Remaining certification gates

1. exact-head CI green;
2. backend runtime local-pair/replay/revocation test green;
3. PC-00 visual certification green;
4. download and inspect BEFORE/AFTER artifacts at 360×800 and 390×844;
5. inspect Chromium + WebKit encrypted vault probes;
6. record visual comparison and score;
7. update canonical docs from IN PROGRESS to VERIFIED only with those proofs;
8. merge with expected-head guard;
9. post-merge verification.

No final PASS is asserted by this document until all gates above are evidenced.
