# P10 — Update signing key ceremony

**Status:** EXECUTED — production public keys admitted and exact-head certified; private keys remain offline.

## Goal

Create and maintain the Digital Crown Ed25519 update-signing trust root without exposing private signing keys to GitHub, CI, ChatGPT, application packages or networked build machines.

## Executed ceremony

Two independent Ed25519 keypairs were generated offline:

- `primary`: operational signing key;
- `recovery`: cold recovery key.

Only the two raw 32-byte public keys and their SHA-256 key IDs were transferred to the repository workflow. Before admission, each public value was Base64-decoded, confirmed to be exactly 32 bytes and its SHA-256 was verified to equal its supplied key ID exactly.

No private PEM or passphrase was supplied to repository/CI/chat.

## Repository admission — CERTIFIED ✅

Both public keys are embedded in `PINNED_UPDATE_KEYS` with status `active`. Runtime re-derives `sha256(raw_public_key)` before accepting a pinned key.

Exact proof:

- admission HEAD `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed`;
- P10 run #49 `33195861612` — SUCCESS;
- artifact `9696388069`;
- digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5`;
- merge proof `05d4ec176e39768521bbfba45746d5c7e38ca67d`, exact merge into P9 base `24965613a02f148d50bcdaee985d34c32373561b`.

## Custody requirements

Private keys remain encrypted and offline.

Recommended custody:

- at least two encrypted physical copies per private key;
- copies stored in physically separate locations;
- strong unique passphrases stored separately from the media;
- recovery key stored separately from operational primary material;
- never upload private key bytes to GitHub Actions, cloud storage, tickets, chat or application files.

## Normal release signing

Routine release manifests are signed using the `primary` private key on a controlled signing machine/process. The manifest `signature.keyid` must equal the SHA-256 of the corresponding raw public key.

The private key is never bundled with Digital Crown.

## Planned primary rotation

1. Generate a new primary pair offline.
2. Ship an authenticated release whose embedded keyring contains old primary + recovery + new primary as `active`.
3. Verify adoption on supported production versions.
4. Switch routine signing to the new primary.
5. Ship a later authenticated release marking the old primary `revoked`.
6. Keep the recovery private key cold unless required.

Do not remove an old trusted key before an already-trusted key has authenticated delivery of its replacement.

## Primary-key compromise

If primary is suspected compromised:

1. stop normal release publication;
2. use the cold recovery key to sign an emergency update;
3. mark the compromised primary `revoked` and introduce a new primary public key;
4. certify unknown/revoked rejection and exact packaged lifecycle before distribution;
5. rotate any related distribution credentials if implicated.

If both active private keys are compromised, in-band trust recovery is insufficient. Re-establish trust out of band.

## Remaining P10 gates

The key ceremony itself is no longer a P10 gate. Remaining blockers are platform distribution credentials/certification and clean-machine evidence:

1. Windows Authenticode production signing + timestamp + real certified apply;
2. macOS Developer ID + notarization/stapling/Gatekeeper + real lifecycle/update;
3. Windows + macOS clean-machine certification;
4. final evidence closeout.

No Vercel.
