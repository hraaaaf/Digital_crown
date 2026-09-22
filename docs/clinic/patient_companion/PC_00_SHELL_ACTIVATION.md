# Patient Companion — PC-00 Local Bridge & Encrypted Device Vault

Status: VERIFIED — exact-head certification completed

## Goal

Deliver the patient-facing Patient Companion shell using the Digital Crown local-first doctrine:

**Cabinet source of truth → one-time QR bridge → encrypted vault on the patient's phone.**

Patient clinical data must not require a cloud patient portal. Firebase is not used as the transport or storage plane for Patient Companion clinical data.

## Success

A patient can:
1. receive a one-time QR/manual pairing secret from the cabinet;
2. pair the phone without a staff account or cabinet JWT;
3. store the resulting Patient Companion context/session inside an encrypted device-local vault;
4. reopen the paired shell while the cabinet is temporarily offline;
5. hold more than one patient context without exposing numeric patient IDs in public URLs;
6. lose future server access immediately when the cabinet revokes the corresponding access.

Observable proof:
- no raw Firebase token field in the patient UI;
- no Patient Companion secret in localStorage/sessionStorage;
- paired state is stored as AES-GCM ciphertext in IndexedDB;
- the AES key is generated non-extractable by WebCrypto and stored as a CryptoKey;
- /api/patient-companion/pair consumes a single-use invitation;
- patient device JWT is scoped to one opaque access_id and cabinet tenant;
- backend router is actually mounted at runtime.

## Corrected BEFORE baseline

The V1 repository already contained:
- Patient Companion models;
- staff administration UI;
- Firebase-oriented activation code;
- appointment/share read APIs.

But the audit found two concrete blockers:
1. backend/main.py did **not** mount patient_companion.router; those endpoints were therefore code-present but not runtime-reachable through the canonical app.
2. the first PC-00 draft exposed a raw Firebase token input and behaved like a cloud portal, contradicting the intended local-first bridge architecture.

Both findings invalidate any earlier claim that the complete Patient Companion flow was already live.

## Architecture

### Pairing plane

Staff:
Patient dossier → Companion → Generate local invitation

Patient:
 /companion → Scan QR or enter manual code → POST /api/patient-companion/pair

Properties:
- invitation is high-entropy / manual fallback;
- one use;
- short lifetime;
- cabinet licence checked locally before binding;
- no Firebase patient token required for local pairing;
- no cabinet staff JWT is ever issued to the patient.

### Device identity plane

Successful pairing creates:
- provider: local_bridge;
- random device subject;
- opaque Patient Companion access;
- signed patient-device token containing only device/access/tenant scope.

Every later server read must re-check:
- active device identity;
- active access;
- matching tenant;
- cabinet licence policy.

Revocation stops future synchronization. It does **not** pretend to remotely erase data already and legitimately stored on the patient's offline device.

### Local storage plane

Browser storage:
- dedicated IndexedDB database: digital-crown-patient-companion;
- random AES-256-GCM CryptoKey generated on-device;
- key marked extractable: false;
- Patient Companion state encrypted before persistence;
- QR/manual secret discarded after pairing;
- no access token copied to localStorage/sessionStorage.

PC-01 must extend this same encrypted vault for synced appointments/documents/media metadata and encrypted payloads. It must not create an unencrypted parallel cache.

## UI target

Baseline viewports:
- 360×800
- 390×844

Flow:
Welcome → QR scanner/manual code → Pairing → Home
and, when multiple contexts exist:
Home entry → Context picker → Home

### Welcome
- clear statement that data stays with cabinet + this phone;
- primary action: Scan QR;
- manual code fallback;
- no email/password/Firebase token field.

### Pairing
- explicit one-time bridge language;
- spinner only while the cabinet verifies the invitation;
- invalid/expired/reused invitation fails closed.

### Home
- patient display name + relationship;
- visible local-vault status;
- PC-01 appointment/document slots clearly marked as not active yet;
- add another patient context;
- explicit “erase this phone” action.

## Security invariants

- No clinical data through Firebase.
- No staff auth/session on patient phone.
- No numeric patient ID in public URL.
- No raw invitation secret after successful pairing.
- No plaintext patient session in Web Storage.
- No fake PC-01+ functionality.
- No Vercel deployment in this lot.
- Offline local possession is intentional; revocation prevents new sync but cannot retroactively delete an offline patient-owned copy.

## Required evidence before close

BEFORE:
- route absent from canonical backend mount;
- no patient-facing route in V1;
- first draft Firebase-token field documented as rejected architecture.

AFTER:
- 360×800 and 390×844 captures for Welcome, Manual Code, Home;
- frontend tests for local-first shell;
- backend contract tests for mount, one-time pairing, scope and revocation;
- build/typecheck;
- exact-head CI;
- adversarial security review;
- canonical Notion + roadmap update.

## Gate

PC-00 closes only when all required evidence above exists and no raw Firebase/cloud patient portal dependency remains in the active patient UI.


## Certification evidence — 2026-09-19

Certified candidate HEAD before this documentation closeout:
`3cfceca5601c7562cb30992ee571d8b736f12ffc`

Exact-head workflow evidence:
- PC-00 Patient Companion Visual Certification run `35471266296`: SUCCESS;
- CI run `35471266310`: SUCCESS;
- Patient P7 `35471266313`: SUCCESS;
- T2 Runtime Browser `35471266293`: SUCCESS;
- UX1-C `35471266320`: SUCCESS;
- V1-07 Commercial Pack Button Matrix `35471266306`: SUCCESS.

Artifact:
- id `10592874065`;
- name `pc00-patient-companion-before-after`;
- digest `sha256:e4f0ff1e392e8a598011ff19afcd8075e1943a28aaf14dedc91f8d6be918da19`;
- 16 matched Chromium/WebKit captures at 360×800 and 390×844;
- no horizontal overflow in AFTER evidence;
- AFTER home vault probes confirm envelope v1, ciphertext present, AES-GCM, non-extractable key, no access-token leak in envelope/Web Storage and no manual-code leak in Web Storage.

Manual artifact inspection:
- Welcome 390×844: QR primary action and manual-code fallback are legible with no staff navigation or raw Firebase token field.
- Home 390×844 Chromium and 360×800 WebKit: patient identity, local-vault state, cabinet reachability action, PC-01 placeholders and destructive erase action are visually separated and fit without horizontal overflow.
- Visual quality score: 8.7/10 for PC-00 scope. Remaining polish is non-blocking and belongs to later wallet/product polish; no fake PC-01 functionality was introduced.

No Vercel deployment.
