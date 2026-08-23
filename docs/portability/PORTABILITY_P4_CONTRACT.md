# Portability P4 — Licence & local secrets cross-platform — contract candidate

Status: **CANDIDATE / NOT CLOSED**

Baseline: `a65d14dddddea3d513913f1453b26c259ef9a7fe`
Branch: `security/portability-p4-license-secrets-rebind`

## Goal

Keep licensing and local secrets secure on Windows and macOS without coupling recoverable clinical data to one machine.

## Verified starting model

The active implementation is `LicenseService` with a local encrypted `license_vault.bin`. The packaged launcher generates a unique `SECRET_KEY` and `CABINET_MASTER_KEY_HEX` on first boot. P3 excludes `.env`, `backup.key` and `license_vault.bin` from the cabinet bundle and declares destination policy `runtime_secrets=regenerate` and `license=rebind`.

The historical roadmap wording about a `LicenseStore`/`license.dat` model is not the implementation observed on this baseline and must not drive P4 behavior.

## Secret classification

| Material | Class | Migration behavior |
| --- | --- | --- |
| Clinical database + covered media | Cabinet-portable | P3 encrypted bundle; restore and re-encrypt on destination |
| Portable runtime preferences | Cabinet-portable | Explicit allow-list only |
| `SECRET_KEY` | Machine-local / regenerable | Never export; generate uniquely on destination; old JWT sessions do not transfer |
| `CABINET_MASTER_KEY_HEX` | Machine-local / regenerable | Never export; generate uniquely on destination |
| `license_vault.bin` | Machine-local proof cache | Never export; copied vault must fail to decrypt under destination key; reacquire/rebind |
| `backup.key` | Machine-local / regenerable | Never export; destination backup key is independent |
| `.env` | Machine-local container | Never export; destination preserves/regenerates its own runtime identity |
| runtime locks / logs / caches | Machine-local ephemeral | Never export |

## Security decisions

1. No hardware fingerprint or OS-specific identity is introduced without a licensing requirement.
2. No predictable cryptographic fallback is permitted for the licence vault.
3. The licence vault key comes only from a strong destination-local `CABINET_MASTER_KEY_HEX` or `SECRET_KEY`.
4. Corrupt, copied-with-wrong-key, missing-key or weak-key vault state fails closed.
5. Offline grace remains 72 hours, but updating the anti-clock-rollback marker must persist successfully; otherwise offline validation fails closed.
6. Licence-vault writes use the existing platform atomic-write boundary. On POSIX this preserves mode `0600`; Windows remains under the per-user application data boundary.
7. Native DPAPI/Keychain storage is not added in P4: the current threat model requires per-machine non-portability and private per-user storage, not hardware binding. Adding native stores now would create platform-specific packaging and recovery behavior without a proven requirement.
8. Licensing failure must never delete, mutate or make the P3 clinical bundle unrecoverable.

## Migration / rebind contract

1. Install/start Digital Crown on the destination machine.
2. Destination first boot creates fresh machine-local runtime secrets.
3. Import the P3 cabinet bundle; source machine secrets remain absent.
4. A source `license_vault.bin`, even if manually copied, is not trusted and is unreadable with the destination key.
5. Licence is reacquired from the authoritative licensing source when online.
6. Successful authoritative validation writes a new destination-local vault.
7. Offline grace can then operate from that new local proof.
8. Because `SECRET_KEY` is destination-local, source-machine JWT sessions are not portable to the destination.

## Success criteria

- no predictable vault key fallback;
- source vault cannot be reused under destination machine key;
- authoritative destination rebind creates a fresh local proof and survives process restart;
- corrupt vault fails closed offline and can recover only through authoritative online validation;
- missing/weak local secret fails closed;
- P3 still excludes machine-bound secrets;
- first boot still regenerates destination secrets;
- same contract passes on Windows, macOS and Linux CI runners.

## Proof gate

`scripts/portability_p4_check.py` executed by `.github/workflows/portability-p1-cert.yml` on:
- `windows-latest`
- `macos-latest`
- `ubuntu-latest`

P4 remains open until the exact final candidate HEAD and tri-OS run are verified. The harness must exercise the real authoritative-validation path that creates the destination-local vault, not a direct test-only vault write.
