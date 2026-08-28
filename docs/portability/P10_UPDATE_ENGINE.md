# P10 — Cross-platform Update Engine

**Status:** ACTIVE — Windows update/rollback/recovery and production trust root certified; final distribution/macOS/clean-machine gates remain. **0 EP credited.**

## Goal
Install only an authentic, fresh, strictly newer Digital Crown release, with verified rescue before mutation, exact package/runtime health verification and automatic rollback.

## Secure-core
- detached Ed25519 manifest signature;
- monotonic sequence + rollback/replay protection;
- issuance/expiration + monotonic trusted time;
- exact OS/architecture target;
- HTTPS + exact size + SHA-256;
- verified encrypted DB rescue before apply;
- atomic non-secret state.

Private update-signing keys are never committed, bundled or read from runtime environment variables.

## Production trust root — CERTIFIED ✅
Two offline-generated Ed25519 keypairs exist: operational `primary` and cold `recovery`. Only their public keys are embedded in `PINNED_UPDATE_KEYS`, both `active`. Runtime requires exactly 32 raw bytes and `sha256(raw_public_key) == keyid`. Unknown/revoked/malformed/mis-keyed keys fail closed; runtime environment cannot replace the trust root.

- product HEAD: `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- P10 #49 `33195861612` — SUCCESS;
- jobs: `secure-core`, `windows-worker`, `windows-packaged-lifecycle` — SUCCESS;
- artifact `9696388069`;
- digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5`;
- merge proof `05d4ec176e39768521bbfba45746d5c7e38ca67d`, exact merge into P9 base `24965613a02f148d50bcdaee985d34c32373561b`.

Ceremony/custody: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.

## Windows lifecycle — CERTIFIED ENGINE ✅
Artifact #49 keeps all required scenarios green after production-key admission:
- positive `1.0.0 -> 1.0.1`, exact package self-test, runtime health and finalization;
- package rollback + SQLCipher DB rescue path;
- interruption recovery back to `1.0.0`;
- target application-start/runtime-bind failure: `UPDATE_WINDOWS_RUNTIME_HEALTH_FAILED` -> worker exit `2` -> package restored `1.0.0` -> rollback health passed; DB rollback not needed for that scenario.

The restored old packaged executable owns SQLCipher rescue decryption/validation. PowerShell never receives the backup key. PostgreSQL rescue remains fail-closed where portable restore semantics are not certified.

## Distribution boundary
The update engine must not turn an uncertified installer into an automatic production mutation.

### Windows Authenticode gate
P6 production signing requires repository secrets:
- `WINDOWS_CODESIGN_PFX_B64`
- `WINDOWS_CODESIGN_PASSWORD`

Workflow behavior: SHA-256 signing, DigiCert timestamping, Authenticode verification. Existing exact evidence remains `P6_AUTHENTICODE=NOT_CONFIGURED` until those production credentials are provisioned.

### macOS distribution gate
P7 `workflow_dispatch` requires:
- `MACOS_DEVELOPER_ID_P12_B64`
- `MACOS_DEVELOPER_ID_P12_PASSWORD`
- `MACOS_CODESIGN_IDENTITY`
- `APPLE_NOTARY_KEY_P8_B64`
- `APPLE_NOTARY_KEY_ID`
- `APPLE_NOTARY_ISSUER_ID`
- `P6_SCIENTIFIC_BUNDLE_SHA256`

It then requires Apple Silicon, Developer ID signing, notarization accepted with no notary errors, stapling, Gatekeeper and install/runtime/upgrade/uninstall smoke.

## Remaining gates before P10 closure
1. signed + timestamped P6 Windows production artifact and real certified apply proof;
2. P7 signed/notarized/stapled/Gatekeeper-verified macOS package and real macOS lifecycle/update proof;
3. Windows + macOS clean-machine certification;
4. final canonical evidence consistency/closeout.

P10 remains **0/13 EP** until all gates are satisfied. No Vercel.
