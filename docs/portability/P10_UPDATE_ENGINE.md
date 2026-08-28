# P10 — Cross-platform Update Engine

**Status:** ACTIVE — Windows update/rollback/recovery and production trust root certified; final distribution/macOS/clean-machine gates remain. **0 EP credited.**

## Goal

Install only an authentic, fresh, strictly newer Digital Crown release, with a verified rescue point before mutation, exact package/runtime health verification and automatic package/DB rollback when required.

## Secure-core contract

P10 does not treat HTTPS or SHA-256 alone as update authentication. Release metadata is a detached Ed25519-signed envelope. The client enforces:

1. signature verification against the embedded production trust root;
2. monotonic positive release sequence and replay/rollback protection;
3. timezone-aware issuance/expiration plus monotonic trusted time;
4. exactly one OS/architecture target;
5. HTTPS, exact size and SHA-256 artifact integrity;
6. verified encrypted DB rescue before apply;
7. atomic, non-secret update state.

The production private signing keys are never committed, bundled or read from runtime environment variables.

## Production trust root — CERTIFIED ✅

The offline ceremony produced two independent Ed25519 keypairs:

- `primary`: normal release signing;
- `recovery`: cold recovery signing path.

Only the two public keys are embedded in `PINNED_UPDATE_KEYS`, both `active`. For every embedded key, runtime Base64-decodes exactly 32 raw Ed25519 bytes and requires `sha256(raw_public_key) == keyid`.

Runtime environment variables cannot replace the production trust root. Unknown, revoked, malformed or mis-keyed entries fail closed. Multiple active keys provide controlled overlap for rotation; this is not threshold signing.

Ceremony/custody procedure: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.

### Exact trust certification

- production-key admission HEAD: `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- PR merge proof: `05d4ec176e39768521bbfba45746d5c7e38ca67d`, exact merge of that HEAD into P9 base `24965613a02f148d50bcdaee985d34c32373561b`;
- P10 run #49 `33195861612` — **SUCCESS**;
- `secure-core` — SUCCESS;
- `windows-worker` — SUCCESS;
- `windows-packaged-lifecycle` — SUCCESS;
- artifact `9696388069`;
- artifact digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5`;
- artifact workflow HEAD: `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`.

No private key or passphrase is present in repository/CI evidence.

## Post-install truth contract

After installer execution, P10 requires two independent truths:

1. the frozen executable passes `--package-self-test` for the exact manifest version, with no forbidden/unqualified scientific assets and `FAIL_CLOSED_NO_WEIGHTS`;
2. loopback `/health` reports runtime and DB healthy.

Only then can installed truth be finalized.

## Windows production apply / rollback — CERTIFIED ENGINE ✅

The Windows engine is fail-closed: frozen `cabinet` runtime, Windows platform, explicit admin confirmation, staged worker hashes, exact artifact/rescue hashes and serialized worker ownership.

Before mutation it validates current package truth, rejects reparse-point install trees, creates/verifies a program snapshot and exports uninstall metadata. After mutation it requires target package self-test, exact target uninstall version and loopback health.

On target failure it restores the exact previous program snapshot and registry metadata, proves the previous package again and requires healthy rollback runtime. DB rescue is used only when the exact old package has been restored but its runtime remains unhealthy for the designated rollback-health reason.

The restored old packaged executable owns SQLCipher rescue decryption/validation; PowerShell never receives the backup key. PostgreSQL rescue remains fail-closed where portable restore semantics are not certified.

## Interruption recovery — CERTIFIED ENGINE ✅

Startup recovery handles `scheduled`, `health_pending`, `applying`, `rolling_back` and controlled DB-rollback states without blind installer re-apply. The real packaged interruption drill is green.

## Exact Windows lifecycle proof #49

`proof.json` from artifact `9696388069` reports overall `status=success` and keeps all required scenarios green after the real production public keys were pinned:

- positive current `1.0.0` → target `1.0.1`, package self-test, runtime health and finalization;
- package rollback + SQLCipher DB rescue path;
- interruption recovery back to `1.0.0`;
- target application-start/runtime-bind failure detected as `UPDATE_WINDOWS_RUNTIME_HEALTH_FAILED`, worker exit `2`, package restored to `1.0.0`, rollback health passed and DB rollback not needed for that scenario.

The earlier #44/#46 evidence remains historical; #49 is the current exact-head product/trust proof.

## Distribution boundary

P6/P7 own platform distribution identity and signing semantics. The update engine must not convert an uncertified installer into an automatic production mutation.

### Windows Authenticode gate

The P6 workflow supports production signing only when these GitHub Actions repository secrets are provisioned:

- `WINDOWS_CODESIGN_PFX_B64`;
- `WINDOWS_CODESIGN_PASSWORD`.

The workflow signs with SHA-256, uses DigiCert timestamping, verifies Authenticode, and otherwise records `P6_AUTHENTICODE=NOT_CONFIGURED`. Existing unsigned P6 evidence does not satisfy this production gate.

### macOS distribution gate

The P7 `workflow_dispatch` requires these repository secrets:

- `MACOS_DEVELOPER_ID_P12_B64`;
- `MACOS_DEVELOPER_ID_P12_PASSWORD`;
- `MACOS_CODESIGN_IDENTITY`;
- `APPLE_NOTARY_KEY_P8_B64`;
- `APPLE_NOTARY_KEY_ID`;
- `APPLE_NOTARY_ISSUER_ID`;
- `P6_SCIENTIFIC_BUNDLE_SHA256`.

The workflow requires Apple Silicon, Developer ID signing, notarization acceptance, notary log without errors, stapling, Gatekeeper assessment and install/runtime/upgrade/uninstall smoke.

## Remaining gates before P10 closure

1. signed + timestamped P6 Windows production artifact and real certified apply proof;
2. P7 signed/notarized/stapled/Gatekeeper-verified macOS package and real macOS lifecycle/update wiring proof;
3. Windows + macOS clean-machine certification;
4. final canonical evidence/consistency closeout.

P10 remains **0/13 EP** until all gates are satisfied. No Vercel.
