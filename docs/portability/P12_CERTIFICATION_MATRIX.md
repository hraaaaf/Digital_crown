# P12 — CI & Certification Matrix

**Status:** CLOSED ✅ — **13 EP credited.**

## Goal

Certify the exact Windows and macOS technical support boundary across runtime, packaging, scientific fail-closed behavior, backup/restore, update/recovery, hardware truth and clean-machine execution before any cross-platform support claim.

## Doctrine

P12 is an evidence aggregator, not a substitute for the owning lots. Closure below consumes independently verified upstream evidence; the P12 static checker only protects the matrix from later truth drift.

P12 technical closure does **not** absorb P13. Human first-launch actions, physical cabinet machines, operational USB/NAS configuration and real-device dental hardware remain P13 where applicable.

## Final certified matrix

| Capability | Windows x64 | macOS arm64 | Owning lot(s) | P12 state |
|---|---|---|---|---|
| Core/runtime + single-instance | certified | certified | P2/P5 | CERTIFIED |
| Frozen/package lifecycle | certified P6/private-PKI successor | certified P7 private distribution | P6/P7/P10 | CERTIFIED |
| Scientific assets/runtime policy | native fail-closed + frozen `FAIL_CLOSED_NO_WEIGHTS` | native fail-closed + frozen `FAIL_CLOSED_NO_WEIGHTS` | P5/P6/P9 | CERTIFIED |
| Hardware truth matrix | conservative boundary certified | conservative boundary certified | P8 | CERTIFIED |
| Disaster recovery | certified macOS → Windows frozen restore | certified Windows → macOS frozen restore | P9 | CERTIFIED |
| Authenticated update | certified signed current → next + rollback | certified private current → next + rollback | P10 | CERTIFIED |
| Launcher/recovery UX | certified | certified shared UX | P11 | CERTIFIED |
| Clean-machine technical E2E | certified on fresh Windows runners | certified on fresh Apple Silicon runners | P6/P7/P9/P10 | CERTIFIED |

## Evidence ledger

### 1. Runtime/startup readiness + single-instance
- P2 candidate `0b6071b663162575efe0de40c411a8ff29763d7a`; Portability Runtime `32601811079` — SUCCESS Windows/macOS/Ubuntu.
- RuntimeSupervisor contract proves exclusive instance lock, reuse/focus of an existing ready instance, fail-closed behavior for an unready locked instance, readiness from `/health`, and UI opening only after readiness.
- Current regression evidence on P10 closeout candidate `a30bec961a6e5fb51f46fd7a5f4b2ed36d7f196e`: Portability Runtime #243 `33274684175` — SUCCESS.

### 2. Frozen/package self-test and forbidden-content policy
- P6 run `32999393374` — SUCCESS: Windows frozen + installed self-tests, no missing required resources, no forbidden secrets, no unqualified scientific weights.
- P7/P10 Clean Hosted `33267234774` — SUCCESS on fresh macOS ARM64 and Windows.
- P9 #11 `33276520623` — SUCCESS: frozen self-test executed on fresh Windows and macOS targets before restore.

### 3. Native/scientific runtime gate + fail-closed capability
- P5 workflow executes native runtime + scientific fail-closed certification on Windows and macOS.
- Current P5 regression on `a30bec961a6e5fb51f46fd7a5f4b2ed36d7f196e`: P5 Native #168 `33274684195` — SUCCESS.
- P6 and P9 frozen self-tests require `scientific_manifest_policy_ok=true`, no unqualified weights and `scientific_capabilities=FAIL_CLOSED_NO_WEIGHTS`.

### 4. Install / upgrade / uninstall + cabinet-data preservation
- Windows P6 run `32999393374` — SUCCESS: clean install, `/health`, upgrade, uninstall, cabinet-data sentinel preservation.
- macOS P7 clean-hosted lifecycle `33267234774` and post-merge P7 #27 `33274684146` — SUCCESS: real DMGs, lifecycle, uninstall data preservation.

### 5. Backup / restore / DR failure scenarios
P9 final technical candidate `4590e2975e71ca89fc404e96e717646155b8fc14`, run `33276520623` — **5/5 SUCCESS**:
- independently persisted off-runner source artifacts;
- distinct fresh opposite-OS targets;
- real frozen packaged Guided Restore in both directions;
- `/health`, SQLCipher integrity, DB marker/user_version and media verification;
- wrong migration secret and ciphertext tamper rejected;
- targeted DR tests retain unavailable destination, disk-full, interrupted/partial and retention failure behavior.

Proof artifacts:
- macOS → Windows `9721759555`, digest `sha256:18d897632b8ee9381b9eec4ca865cdf419164b1950cf83294f06c86075f0830f`;
- Windows → macOS `9721742568`, digest `sha256:d62d1e0e6d69fbff7b5e3e58d877e932fd53ea2b5ee04c42d05cd98199ddfc09`.

### 6. Authenticated update current → next + rollback
P10 clean-hosted and exact-head regressions prove:
- signed manifest + exact package identity/hash/size;
- Windows private-PKI Authenticode + RFC3161 timestamp lifecycle;
- macOS signed-manifest + exact DMG + strict ad-hoc integrity lifecycle;
- target package self-test, `/health`, interruption recovery, package rollback and DB rollback.

Exact P10 closeout candidate `a30bec961a6e5fb51f46fd7a5f4b2ed36d7f196e`:
- P10 #141 `33274684115` — SUCCESS;
- P10 macOS #59 `33274684087` — SUCCESS;
- Clean Hosted #9 `33274684081` — SUCCESS.

### 7. Launcher/recovery regression
P11 candidate `cbaf21a066fb6b8b70f4c9d6b3ec1a950cda890b`, run `32783305559` — SUCCESS, with runtime supervisor tests, frontend build and verified recovery surfaces. Current P11 regression #119 `33274684098` — SUCCESS.

### 8. Artifact identity / checksum / platform trust truth
- Windows P6/P10 retain exact installer identity/hash and private-PKI signing truth without SmartScreen reputation claims.
- macOS P7/P10 retain exact DMG hash/size, bundle identity/version and strict ad-hoc codesign integrity without Developer ID/notarization claims.

### 9. Clean-machine technical execution
- Windows: P6 clean install + P10 Clean Hosted + P9 fresh Windows target all start frozen runtime and prove health.
- macOS: P7/P10 clean ARM64 runner + P9 fresh macOS target all start frozen runtime and prove health.
- This is technical clean-machine evidence only; real physical cabinet ceremony remains P13.

### 10. Hardware support truth
P8 is CLOSED 21 EP. No direct dental device is certified as `SUPPORTED`; file-import/limited/unsupported states remain explicit. Any future `SUPPORTED` promotion still requires real-device evidence on every claimed OS.

## P13 boundary retained

P12 does not claim:
- human `Open Anyway` / administrator first-launch success on a physical Mac;
- operational USB/NAS durability, permissions or handling in a real cabinet;
- real dental-device acquisition support where P8 remains FILE-IMPORT/LIMITED/UNSUPPORTED;
- public Apple notarization or Microsoft SmartScreen reputation.

Those claims are not technical P12 requirements and remain P13/product-distribution boundaries.

No Vercel.
