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
### Windows Authenticode — private Digital Crown PKI, zero-cost
Production mutation remains `apply_certified=false` until the exact installer has a valid Authenticode signature and timestamp certificate.

Digital Crown uses a private code-signing certificate generated offline. This is a private trust model for known clinic machines, not public Microsoft/SmartScreen publisher reputation.

GitHub Actions repository secrets:
- `WINDOWS_CODESIGN_PFX_B64`
- `WINDOWS_CODESIGN_PASSWORD`

Repository variable:
- `WINDOWS_CODESIGN_CERT_SHA256`

The workflow:
1. fails closed on partial configuration;
2. imports the PFX only into the ephemeral runner;
3. requires Code Signing EKU `1.3.6.1.5.5.7.3.3`;
4. exports the public certificate and verifies its exact SHA-256 pin;
5. trusts that public certificate only inside the ephemeral runner for verification;
6. signs with SignTool using SHA-256 and timestamping;
7. requires `Get-AuthenticodeSignature` status `Valid` and a timestamp certificate;
8. removes PFX, CER and temporary certificate-store entries from the runner.

On each clinic Windows machine, the public `.cer` must be installed once in LocalMachine `Root` and `TrustedPublisher` before the private signature is considered trusted. The private PFX/password are never installed on clinic machines.

Current evidence remains `P6_AUTHENTICODE=NOT_CONFIGURED` until the private certificate ceremony and GitHub secret provisioning are complete.

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
1. Generate the private Windows code-signing certificate offline; pin its public SHA-256; provision GitHub secrets; certify signed + timestamped Windows artifact and real P10 apply.
2. Install the public signing certificate on clean Windows clinic test machine and certify trust + lifecycle.
3. macOS signed/notarized/stapled/Gatekeeper lifecycle/update.
4. clean-machine macOS and final evidence closeout.

Ceremony/custody: `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.

No Vercel.
