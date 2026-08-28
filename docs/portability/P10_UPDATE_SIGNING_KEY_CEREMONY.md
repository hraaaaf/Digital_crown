# P10 — Update signing key ceremony

**Status:** PROCEDURE READY — production secrets not generated in repository or CI.

## Goal

Create the Digital Crown Ed25519 update-signing trust root without ever exposing a private signing key to GitHub, CI, ChatGPT, the application package or a networked build machine.

## Success

The ceremony is successful only when:

1. two independent Ed25519 keypairs exist: an operational signing key and a cold recovery key;
2. both private keys exist only in encrypted offline custody;
3. only the two 32-byte raw public keys and their SHA-256 key IDs leave the offline ceremony;
4. the two public keys are pinned in `PINNED_UPDATE_KEYS` as `active`;
5. an exact-head P10 secure-core run proves both active keys are accepted, unknown/revoked keys are rejected and environment variables cannot replace the trust root;
6. the exact packaged lifecycle remains green after pinning;
7. no private key material appears in repository history, CI logs, artifacts, issues, PRs, chat or application files.

## Why two keys

Digital Crown currently accepts a single Ed25519 signature per manifest, so this is **not threshold signing**. Pinning two active public keys provides a practical recovery path:

- `primary`: used for normal release signing;
- `recovery`: private half kept cold/offline and not used for routine releases.

If the primary key must be revoked, a release can still be authenticated by the already-pinned recovery key and can ship a new keyring. Compromise of any active signing key is still security-critical; this design does not claim TUF-style threshold compromise resistance.

## Ceremony environment

Use a dedicated computer that can be taken offline for the entire generation/export operation.

Before disconnecting, install a current supported Python and `cryptography` package from trusted sources. Then disconnect networking before generating either private key.

Recommended custody:

- encrypted removable media or hardware-backed encrypted storage;
- two physically separate encrypted backup copies for each private key;
- strong unique passphrase stored separately from the media;
- recovery-key media stored separately from the operational-signing-key media.

Never place private key bytes in GitHub Actions secrets merely to make the ceremony convenient. CI is a distribution/build environment, not the root-of-trust ceremony environment.

## Offline generation script

Create this script only on the offline ceremony machine and run it once for `primary` and once for `recovery`.

```python
from __future__ import annotations

import base64
import getpass
import hashlib
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

name = input("Key name (primary/recovery): ").strip()
if name not in {"primary", "recovery"}:
    raise SystemExit("invalid key name")

password = getpass.getpass("Private-key encryption passphrase: ").encode("utf-8")
if len(password) < 16:
    raise SystemExit("passphrase too short")

private_key = Ed25519PrivateKey.generate()
public_raw = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(password),
)

key_id = hashlib.sha256(public_raw).hexdigest()
public_b64 = base64.b64encode(public_raw).decode("ascii")

Path(f"digitalcrown-update-{name}.private.pem").write_bytes(private_pem)
Path(f"digitalcrown-update-{name}.public.txt").write_text(
    f"keyid={key_id}\npublic_key_b64={public_b64}\n",
    encoding="ascii",
)

print(f"keyid={key_id}")
print(f"public_key_b64={public_b64}")
print("PRIVATE KEY WRITTEN LOCALLY; DO NOT COPY IT TO A CONNECTED MACHINE")
```

The public key is exactly 32 raw Ed25519 bytes before Base64 encoding. Digital Crown defines `keyid = sha256(raw_public_key).hexdigest()`.

## Offline verification before export

For each public record:

1. Base64-decode `public_key_b64` and confirm it is exactly 32 bytes.
2. Recompute SHA-256 of those 32 bytes.
3. Confirm the resulting lowercase hexadecimal digest equals `keyid` exactly.
4. Confirm the encrypted private PEM can be opened with its passphrase.
5. Create the physically separate encrypted custody copies.
6. Remove temporary plaintext/public working files from the offline machine if they are no longer required.

Only these values may be transferred to the connected development machine:

```text
primary.keyid
primary.public_key_b64
recovery.keyid
recovery.public_key_b64
```

Private PEM files and passphrases must not leave offline custody.

## Repository admission

After the human ceremony, edit only the public keyring in `backend/services/update_engine.py`:

```python
PINNED_UPDATE_KEYS = {
    "<primary-keyid>": {
        "public_key_b64": "<primary-public-key-b64>",
        "status": "active",
    },
    "<recovery-keyid>": {
        "public_key_b64": "<recovery-public-key-b64>",
        "status": "active",
    },
}
```

Admission checks before commit:

- both Base64 values decode to exactly 32 bytes;
- dictionary key equals SHA-256 of raw public key;
- no private material is present;
- `DIGITALCROWN_UPDATE_PUBLIC_KEY_B64` remains unusable as a production trust override;
- existing unknown/revoked fail-closed tests remain green;
- add exact tests for both admitted production public keys without storing either private key.

## Normal release signing

Routine manifests are signed by the `primary` private key on a controlled signing machine/process. The private key is never bundled with Digital Crown.

The signed envelope must retain the exact public-key SHA-256 in `signature.keyid`; clients select the matching pinned key and verify Ed25519 before trusting release metadata.

## Rotation

Planned primary rotation:

1. generate a new primary keypair offline;
2. while old primary/recovery are still trusted, ship a release whose embedded keyring contains old primary + recovery + new primary as `active`;
3. verify adoption on supported production versions;
4. switch routine signing to the new primary;
5. ship a later authenticated release marking the old primary `revoked`;
6. retain recovery private key cold unless recovery is required.

Do not remove an old trusted key from clients before a release signed by an already-trusted key has delivered the replacement trust state.

## Primary-key compromise

If primary is suspected compromised:

1. stop normal release publication;
2. use the cold recovery key to sign the emergency update;
3. emergency update must mark the compromised primary `revoked` and introduce a new primary public key;
4. certify unknown/revoked rejection and exact packaged lifecycle before broad distribution;
5. rotate any distribution credentials implicated in the incident.

If **both pinned active private keys** are compromised, normal in-band trust recovery is no longer sufficient. Treat recovery as out-of-band re-establishment of trust and do not claim the existing updater can safely repair that condition by itself.

## P10 gate after ceremony

After the two public keys are admitted:

1. run P10 secure-core on the exact HEAD;
2. inspect tests for primary/recovery acceptance and revoked/unknown rejection;
3. run the exact packaged Windows lifecycle once on that final keyring HEAD;
4. update PR #239 and canonical status evidence;
5. keep P10 at 0/13 EP until P6 signed production artifact, P7 signed/notarized macOS lifecycle and clean-machine Windows/macOS gates are also satisfied.

## References

- The Update Framework specification, key management and migration: offline storage for high-value signing keys and explicit key replacement/revocation.
- OpenSSL documentation: Ed25519 is a supported key-generation algorithm.
- `cryptography` Ed25519 documentation: raw Ed25519 public serialization is 32 bytes and supports `Encoding.Raw` / `PublicFormat.Raw`.

No Vercel.
