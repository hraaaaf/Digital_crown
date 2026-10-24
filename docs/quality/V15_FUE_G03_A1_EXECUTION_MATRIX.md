# FUE-G03 — Phase A / Chantier 1 — First-use identity and QR (2026-10-24)

**Status: PREVIOUS TECHNICAL GREEN at b83bb24; new A1 visual corrections CANDIDATE / NOT CERTIFIED until exact-head CI and explicit human approval.**

## Base and isolation

- Derived from previously observed GREEN candidate **PR #1057 @ `44625de39cbff8e82424bc59faa4dc0af45a014d`**, without mutating that PR.
- This is a **stacked DRAFT PR** targeting branch `test/v15-fue-g02-g03-risk-matrix-20261024`. It must not be merged ahead of its base or silently retargeted.
- The actual repository `master` may be newer; no assertion that the isolated test code is the latest master.
- **Only synthetic accounts and patients** in freshly created `t2-runtime-cert.db`. Guard `ENVIRONMENT=test`, `T2_STATION_FUE=1`, `T2_G03_A1=1`, `DIGITALCROWN_ISOLATED_RUNTIME=1`, exact SQLite URL. No external patient data, no production/station device access or Vercel.
- Genuine Chromium browsers, FastAPI localhost HTTP and SQLCipher SQLite. The phone's app uses its **actual Patient Companion pairing UI and encrypted IndexedDB**.
- On **Linux CI**, the default remote key enrollment correctly returns `503 Protection OS des clés distantes indisponible` because Cabinet OS-bound protection is unavailable. Do NOT bypass the server key-protection policy. This particular test uses the product-supported **local-only Companion** capability profile: `crypto.randomUUID` is absent in the synthetic Chromium phone context, while WebCrypto `subtle` (AES-GCM) and IndexedDB remain fully available. No HTTP mocks, no production security change. This establishes local-first real pairing and QR Station handoff only, **not default remote-key enrollment / OS-bound private-key protection**.
- Credentials and QR bearer links are used only in memory; sanitized HTTP logs must never include headers, response bodies, tokens or query strings.

## Criteria with exact oracles

| ID | Case | Observable proof and limits |
|---|---|---|
| A1-01 | Cold/unpaired device | Fresh browser navigates to the REAL data-free `/hub?select=1` first-use/recovery surface, waits for visible Hub and Station card (not a blank bootstrap frame), screenshot and no patient record. Authenticated first-login UI path remains a separate gap. |
| A1-02 | Second station enrollment via owner's pairing code | Distinct HttpOnly workstation identity, one-use code, replay DENY, owner PIN, owner revocation; includes existing backend pair/migration tests. |
| A1-03 | Phone app pairs to patient via one-use manual invitation | Staff issues genuine invitation for two fictitious patient contexts; actual phone UI calls /pair twice, vault encryption remains product code, screenshot. This is *phone setup by manual invitation*, not camera-scanned QR pairing. |
| A1-04 | Kiosk QR handoff → separate paired Companion browser → Station arrival | Station posts explicit `purpose=appointment`; purpose is integrity-bound in the hashed one-shot QR token, cannot be edited in the URL. Backend claim returns confirmed purpose; Companion shows **Aujourd’hui + arrival guidance**, NOT document withdrawal. Real claim 200, Station arrival 200, independent SQL. |
| A1-05 | Adversarial claims | Unidentified Station arrival 409, wrong-workstation read 404/423, replay 409, invented QR bearer 409, expired session 409 (test-only SQL expiry), revoked station cannot be claimed 409 or read station feed 423. A tampered purpose suffix must fail 409 rather than change patient UX. |
| A1-06 | Previous API security contracts | Existing backend fallback/tenant/expiry tests + React StrictMode. Additional real `purpose=documents` Companion claim preserves **Documents + retrait** and old empty-body Station clients default to document intent. No migration or staff access broadening. **Do not mark PASS before current SHA CI executes.** |

## Negative and future scopes

- Actual **optical scan** of the QR by a phone camera, NFC hardware handshake, non-loopback HTTPS/TLS on two physical devices, Windows kiosk lockdown/real LAN are **V1.5-10 RPG-P**, NOT certified by localhost harness.
- This phase tests **real QR URL handoff** (non-mocked Companion) while manual pairing uses a genuine invitation. Hardware scanner is never claimed.
- A1 is **not** Phase B session/network resilience, nor Phase A chantier 3 RDV/Wall deep edge cases. Those stay OPEN.
- The former human visual approval of #1057 images does not automatically approve new A1 screenshots.

## Gate decision

1. Read GitHub run logs on the exact SHA and collect test execution counts (including skipped).
2. Verify screenshot ZIP, all expected before/after images, sanitized HTTP and independent `sql-after.json`.
3. Verify correct authorization errors and no bearer secret in artifacts.
4. Record any RED as open with trace and corrective exact SHA; no AUTO GREEN.
5. Obtain separate human validation of new screenshots before visual closeout. NO merge/deploy unless explicitly authorized.

## Approval checkpoint — 24 October 2026

The user authorized correction of the TWO visual discrepancies and fresh exact-SHA evidence. This is **not** an implicit sign-off on future screenshots. Prior human gate fails closed on every HEAD change. New capture must be inspected by the reviewer and approved explicitly, or remain OPEN. Product intent is bound into random server-generated handoff bearer and its stored SHA-256 hash. The intent is a **presentation/routing hint**, NOT new authorization for documents; all existing document eligibility gates remain unchanged. Production Windows protected remote keys remain a separate gate.
