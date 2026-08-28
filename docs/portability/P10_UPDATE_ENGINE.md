# P10 — Cross-platform Update Engine

**Status:** ACTIVE — Windows update/rollback/recovery and production trust root certified; distribution/macOS/clean-machine gates remain. **0/13 EP.**

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
- interruption recovery;
- target-start/runtime-bind failure: `UPDATE_WINDOWS_RUNTIME_HEALTH_FAILED` -> worker exit 2 -> restore `1.0.0` -> healthy rollback; DB rollback not required in this scenario.

## Distribution gates
### Windows Authenticode
Required GitHub Actions repository secrets:
- `WINDOWS_CODESIGN_PFX_B64`
- `WINDOWS_CODESIGN_PASSWORD`

Current evidence remains `P6_AUTHENTICODE=NOT_CONFIGURED`. When configured, workflow signs SHA-256, timestamps via DigiCert and verifies Authenticode.

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
1. Windows signed + timestamped production artifact and real certified P10 apply.
2. macOS signed/notarized/stapled/Gatekeeper lifecycle/update.
3. clean-machine Windows + macOS.
4. final evidence closeout.

Ceremony/custody: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.

No Vercel.
