# P10 — Cross-platform Update Engine

**Status:** ACTIVE — Windows update/rollback/recovery and production trust root certified; distribution/macOS/clean-machine gates remain. **0 EP credited (0/13 EP).**

## Goal
Install only an authentic, fresh, strictly newer Digital Crown release with verified rescue, exact package/runtime health and automatic rollback.

## Certified product proof ✅
- product HEAD `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- P10 #49 `33195861612` — SUCCESS;
- secure-core + Windows worker + packaged lifecycle — SUCCESS;
- artifact `9696388069`;
- digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5`;
- merge proof `05d4ec176e39768521bbfba45746d5c7e38ca67d`, exact merge into base P9 `24965613a02f148d50bcdaee985d34c32373561b`.

## Production trust root ✅
Two real Ed25519 keypairs were generated offline: operational `primary` and cold `recovery`. Only public keys are embedded in `PINNED_UPDATE_KEYS` as active. Runtime requires 32 raw bytes and `sha256(raw_public_key) == keyid`; unknown/revoked/malformed/mis-keyed values fail closed; runtime environment cannot replace the trust root. Private keys/passphrases remain offline.

## Windows lifecycle ✅
#49 proves after real trust-key admission:
- positive `1.0.0 -> 1.0.1`;
- exact package self-test;
- runtime health and finalization;
- package rollback + SQLCipher DB rescue;
- interrupted apply recovery;
- program snapshot + uninstall registry restoration;
- target-start/runtime-bind failure: `UPDATE_WINDOWS_RUNTIME_HEALTH_FAILED` -> worker exit 2 -> restore `1.0.0` -> healthy rollback; DB rollback not required in this scenario;
- the old packaged executable owns last-resort DB rescue; PostgreSQL restore remains fail-closed/unsupported by the local-file bridge.

Packaging dependency remains **P6/P7**. The Windows external worker contract targets native **Windows PowerShell 5.1**. After exact package self-test, runtime truth is the loopback **`/health`** endpoint with runtime and DB both healthy.

## Distribution gates
### Windows Authenticode — DigiCert KeyLocker selected
Production mutation remains `apply_certified=false` until the exact installer has a valid Authenticode signature and timestamp certificate.

The public code-signing private key must remain inside DigiCert KeyLocker/HSM. GitHub receives only CI authentication material:

Repository secrets:
- `DIGICERT_SM_API_KEY`
- `DIGICERT_SM_CLIENT_CERT_FILE_B64`
- `DIGICERT_SM_CLIENT_CERT_PASSWORD`

Repository variables:
- `DIGICERT_SM_HOST`
- `DIGICERT_KEYPAIR_ALIAS`

`DIGICERT_SM_CLIENT_CERT_FILE_B64` is a DigiCert ONE client-authentication certificate, not the code-signing private key. The signing private key is never exported to GitHub Actions.

Current evidence remains `P6_AUTHENTICODE=NOT_CONFIGURED`. The selected workflow path is DigiCert Binary Signing / KeyLocker, SHA-256, timestamp required, followed by local Authenticode verification.

### macOS P7
Required secrets:
- `MACOS_DEVELOPER_ID_P12_B64`
- `MACOS_DEVELOPER_ID_P12_PASSWORD`
- `MACOS_CODESIGN_IDENTITY`
- `APPLE_NOTARY_KEY_P8_B64`
- `APPLE_NOTARY_KEY_ID`
- `APPLE_NOTARY_ISSUER_ID`
- `P6_SCIENTIFIC_BUNDLE_SHA256`

Required proof: Apple Silicon, Developer ID, notarization accepted/no errors, stapling, Gatekeeper, install/runtime/upgrade/uninstall smoke and real update lifecycle.

## Remaining gates
1. DigiCert KeyLocker account/certificate provisioned; exact Windows artifact signed + timestamped and real certified P10 apply.
2. macOS signed/notarized/stapled/Gatekeeper lifecycle/update.
3. clean-machine Windows + macOS.
4. final evidence closeout.

Ceremony/custody: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.

No Vercel.
