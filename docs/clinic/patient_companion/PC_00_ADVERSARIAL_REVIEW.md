# PC-00 — Adversarial Review

Status: VERIFIED — adversarial gates closed on certified candidate.

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

Status: VERIFIED by exact-head CI/runtime certification.

### F-02 — First PC-00 draft behaved like a Firebase token portal
Severity: blocker / architecture violation

Observed:
first draft UI asked for a raw Firebase ID token.

Risk:
contradicted the approved local-first QR bridge doctrine and created unnecessary cloud/auth coupling.

Remediation:
remove Firebase token UI from canonical Patient Companion flow. Canonical pairing is QR/manual one-shot local bridge. Legacy Firebase activation code remains compatibility-only and is not used by the active patient shell.

Status: VERIFIED by exact-head frontend + visual certification.

### F-03 — Patient session must not be plaintext Web Storage
Severity: high

Risk:
localStorage/sessionStorage are easy accidental leak surfaces and are shared with unrelated web auth conventions in the desktop app.

Remediation:
dedicated IndexedDB vault, AES-256-GCM, WebCrypto non-extractable CryptoKey, encrypted state envelope. Patient Companion does not write its token or manual code to localStorage/sessionStorage.

Required proof:
real browser IndexedDB inspection in Chromium and WebKit after pairing.

Status: VERIFIED by Chromium + WebKit artifact storage probes.

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

Status: VERIFIED by exact-head CI.

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

Status: VERIFIED by exact-head CI/runtime certification.

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

Status: VERIFIED by exact-head CI.

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

## Certification closeout

Certified candidate HEAD before documentation closeout:
`3cfceca5601c7562cb30992ee571d8b736f12ffc`

Evidence:
- PC-00 visual run `35471266296`: SUCCESS;
- CI `35471266310`: SUCCESS;
- T2 `35471266293`: SUCCESS;
- P7 `35471266313`: SUCCESS;
- artifact `10592874065`, digest `sha256:e4f0ff1e392e8a598011ff19afcd8075e1943a28aaf14dedc91f8d6be918da19`;
- 16 matched Chromium/WebKit screenshots inspected at 360×800 and 390×844;
- encrypted-vault probes passed: AES-GCM, non-extractable key, ciphertext envelope, no patient token/manual-code Web Storage leak;
- no horizontal overflow;
- visual scope score: 8.7/10.

The non-extractable WebCrypto key remains a browser-origin control, not hardware-backed/XSS-proof storage. Revocation still prevents future sync and does not claim retroactive deletion of offline patient-owned copies.

No Vercel deployment.
