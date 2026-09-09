# P10 — Update signing key ceremony

**Status:** EXECUTED — production public keys admitted and exact-head certified; private keys remain offline.

## Goal
Maintain the Digital Crown Ed25519 update-signing trust root without exposing private signing keys to GitHub, CI, chat, application packages or networked build machines.

## Executed ceremony
Two independent Ed25519 keypairs were generated offline:
- `primary`: operational signing key;
- `recovery`: cold recovery key.

Only the public values entered the repository workflow. Before admission, each Base64 public value decoded to exactly 32 bytes and its SHA-256 equaled the supplied key ID. No private PEM or passphrase was supplied to repository/CI/chat.

## Repository admission — CERTIFIED ✅
Both public keys are embedded in `PINNED_UPDATE_KEYS` as `active`. Runtime re-derives `sha256(raw_public_key)` before accepting a key.

Exact proof:
- admission HEAD `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- P10 #49 `33195861612` — SUCCESS;
- artifact `9696388069`;
- digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5`;
- merge proof `05d4ec176e39768521bbfba45746d5c7e38ca67d` into P9 base `24965613a02f148d50bcdaee985d34c32373561b`.

## Custody
- keep private keys encrypted and offline;
- keep physically separate encrypted backups;
- store passphrases separately from media;
- keep recovery material separate from primary material;
- never upload private key bytes to GitHub Actions, cloud storage, tickets, chat or application files.

## Normal signing
Routine manifests use `primary`. `signature.keyid` equals SHA-256 of the corresponding raw public key. The private key is never bundled with Digital Crown.

## Rotation
1. Generate new primary offline.
2. Deliver an authenticated release trusting old primary + recovery + new primary.
3. Verify adoption.
4. Switch routine signing to new primary.
5. Deliver a later authenticated release marking old primary `revoked`.
6. Keep recovery private key cold unless required.

Never remove an old trusted key before an already-trusted key has authenticated delivery of its replacement.

## Primary compromise
Stop normal publication, use cold recovery to authenticate an emergency release, revoke compromised primary, introduce a new primary, then recertify fail-closed trust + packaged lifecycle. If both active private keys are compromised, re-establish trust out of band.

## Remaining P10 gates
The key ceremony is closed. Remaining gates are:
1. Windows Authenticode production signing + timestamp + real certified apply;
2. macOS Developer ID + notarization/stapling/Gatekeeper + real lifecycle/update;
3. Windows + macOS clean-machine certification;
4. final evidence closeout.

No Vercel.
