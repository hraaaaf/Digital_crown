# V1.5-04.5 / 04.6 — Reality proof, two adversarial perspectives (2026-10-12)

**Status: OPEN until exact-HEAD CI and field/human gates.** The two perspectives below are **internal adversarial reviews**, not independent external reviewers. No merge or deployment is authorized.

## Current, corrected product contract

1. The practitioner finalizes the exact care-sheet PDF with verified hash and explicitly authorizes withdrawal.
2. An enrolled shared **Station** creates a 120-second opaque QR/NFC identity session. The paired patient's **Companion phone** claims the session once with patient-device auth and matching accessId.
3. The Station only displays eligibility metadata / staff fallback messaging; **the Station PDF endpoint fails closed with HTTP 423** and the frontend never creates a Station PDF Blob or local download.
4. A *separate authenticated patient-facing endpoint* lists and downloads only eligible care sheets for the same tenant + patient + exact claiming Companion access, while the Station session and workstation remain active. PDF contents must pass trusted finalizer/hash verification, audit patient access, and use private no-store, nosniff PDF headers.
5. Phone **Terminer et effacer ma session** attempts to revoke the server-bound session immediately; if offline, it clears the local UI and explicitly says server revocation could not be confirmed. Exit on Station and the 120-second TTL remain fail-closed boundaries.
6. Unpaired manual Station fallback never advertises phone pickup. Real printing and phone app integration beyond authorized care sheet remain outside this lot; never claim them as delivered.

## Evidence tiers — do not conflate

- **RPG-C:** FastAPI/SQLite tests covering other patient/access, authorization, forgery/tampered PDF, wrong Station, QR replay, unauthenticated phone, no-phone fallback, revoked patient/station, expiry/purge, and authenticated phone self-revocation. These must be executed on the **exact** candidate SHA.
- **RPG-X:** Actual Uvicorn TLS 1.3 server in an isolated runner, two independently enrolled workstation credentials, distinct Cabinet/Station/Companion client **OS processes**, verified certificate, SHA-256 match, PDF render with PyMuPDF, phone receiver, negative authorization and purge. This is **not two physical devices**.
- **RPG-J (Station):** 48 BEFORE + 48 AFTER paired screenshots across FR/EN/AR, 390/430/768/1280 and normal/text200, synthetic QR/API backend, zero kiosk PDF requests/buttons and no horizontal overflow. The BEFORE base is pinned to `f32af204ecb8845008080afd5a49ed8d1582eb9b`.
- **RPG-J (Companion, new candidate):** 8 BEFORE + 8 AFTER screenshots of the real Patient Companion React app with encrypted fake IndexedDB pairing, simulated claim and authenticated document discovery, matching viewports and normal/text200. No real hardware or backend is used by the screenshot harness. The genuine patient TLS download is separately certified in RPG-X.
- **RPG-P / hardware:** **OPEN.** Physical Cabinet PC + distinct Station PC + actual patient-owned phone over the cabinet LAN/HTTPS, QR camera/NFC, download, offline/expiry/purge, and if supported secure local printing all need witnessed proof.

## A — internal security & privacy adversarial review

| Finding | Severity | Response |
| --- | --- | --- |
| Shared Station previously offered clinical PDF download and persisted it in Downloads | **BLOCKER** | Workstation PDF route now returns HTTP 423; kiosk service/button removed; real PDF restricted to claimed Companion |
| Sender and Station were initially represented by the same workstation credentials in early rehearsal | **BLOCKER** | Distinct real workstation enrollment identities enforced in RPG-X |
| Scanned QR token alone could be incorrectly perceived as a PDF credential | **BLOCKER** | Patient bearer access and exact session claim required separately; bearer-only and wrong patient/access denied |
| Phone close previously only hid UI without server revocation | **MAJOR** | New scoped Companion POST /purge; server clears patient IDs and expires access; offline UI displays local-only status honestly |
| Patient name could remain on unattended Station after session expiry | **MAJOR** | Timed client cleanup and server TTL/purge tests |
| Actual physical phone/device origin cannot be cryptographically inferred from HTTP bearer alone | **OPEN FIELD** | Encrypted paired Companion vault and patient auth are checked; physical possession, LAN deployment and access management need field evidence |

**A provisional score: 7.5/10** — security policy and test matrix implemented; **not clean until exact-HEAD green CI and field checks**.

## B — internal test fidelity, UX and evidence review

| Finding | Severity | Response |
| --- | --- | --- |
| Old harness demanded obsolete Station construction copy / local PDF download | **MAJOR** | Tests and Playwright capture now explicitly prohibit any Station PDF |
| Only Station UI captured, while actual new download controls live on Companion | **MAJOR** | Added real encrypted IndexedDB Companion UI capture across eight matched BEFORE/AFTER viewports, pending CI |
| Earlier report called one-runner TLS “two devices” | **BLOCKER** | Explicit separate OS processes vs physical device scope; hardware gate remains OPEN |
| Manual fallback could advertise phone delivery without an app pairing | **MAJOR** | Station API `companionPaired` and conditional UI; backend patient access bound to claim ID |
| UI said “Fermer la session” but did not revoke it | **MAJOR** | Revocation endpoint + honest offline failure messaging, tested |
| User-facing visual approval must be for this exact HEAD | **OPEN HUMAN** | Publish screenshots and receive explicit human authorization; only then apply `visual-approved-by-achraf` |

**B provisional score: 7.2/10** — fixes staged; **not clean until both screenshot sets and tests pass on one SHA**.

## Mandatory closeout

- Verify required exact-HEAD workflows, downloaded JSON artifacts, and patient-free screenshots. A prior green SHA does not certify later commits.
- Inspect visually BEFORE/AFTER on identical viewports in all Station languages and the phone screen; inspect text200 for clipping/RTL/overflow. Do not use a green image-generation workflow as a human approval.
- Obtain witnessed true 3-device LAN/TLS and actual phone download + kiosk Downloads check, with SHA-256; keep QR/NFC/printing unsupported modalities marked OPEN if not verified.
- Only upon user explicitly approving the exact-HEAD AFTER screenshots may the reviewer apply `visual-approved-by-achraf`. Every subsequent HEAD requires re-approval.
- Update Notion/canonical docs, re-run two internal perspectives on the same exact SHA and check no remaining BLOCKER/MAJOR before any convergence claim. **NO MERGE, NO DEPLOY without explicit authorization.**

**Scores are provisional and severe.** Draft implementation and clean CI are not the same as a fully certified field rollout.
