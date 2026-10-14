# LOT06-H — Windows DPAPI CurrentUser custody laboratory (NOT production)

Status: OPEN / synthetic security work only. Source: PR #851 on the LOT06 branch. This adds an isolated Windows key-vault prototype; it does NOT switch the acquisition CLI away from its legacy environment-supplied key, change spool wire format, or authorize Windows installation.

## Boundary and threat model

- Random 256-bit spool-key candidate is sealed using native Windows CryptProtectData with CRYPTPROTECT_UI_FORBIDDEN, scope CurrentUser, never CRYPTPROTECT_LOCAL_MACHINE. A deterministic cabinet/workstation identity fingerprint is required as optional DPAPI entropy. The JSON contains only the hash of that scope and DPAPI ciphertext, not patient identifiers, plaintext keys, or source filenames.
- Plaintext is returned only to the calling Python process on explicitly authorized unlock. CryptUnprotectData memory is zeroed before LocalFree; Python byte copies remain in process memory (not guaranteed zeroizable). The sample module MUST NOT be used with real clinic credentials/media.
- The existing LOT06-G read-only preflight remains BLOCKED regardless of DPAPI laboratory success. Disk ACL, Windows service logon/account lifecycle, profile availability, key isolation from local administrators, offline backups, endpoint protection, and physical NTFS/hardware remain unverified. This module is intentionally NOT wired into the current CLI.
- A file-side local revocation tombstone prevents unlock and same-path restore while present. An administrator or rollback of local storage can remove/replace it; it is NOT durable central revocation, cryptographic erasure, machine deactivation, or authorization revocation. A future signed authoritative revocation ledger is required.
- Backup contains ONLY the sealed DPAPI envelope. Recovery is demonstrated on the same Windows user and available DPAPI profile/master keys; backup alone cannot recover keys after loss of the Windows profile, DPAPI master keys, workstation or service account. This is a real fail-closed limit, not an escrow solution.
- Existing DC6A encrypted spool blobs carry NO key identifier. Changing the key would make existing pending captures inaccessible. Therefore rotate_existing_spool unconditionally refuses with ROTATION_REQUIRES_VERSIONED_SPOOL_AND_REWRAP. Future migration must use versioned envelopes, atomic verified rewrap of backlog, previous-key retention, crash recovery and independent rollback tests.
- Paths and destination ACLs must be checked by an independently authorized Windows install process. This lab does not enforce NTFS ACLs and does not claim protection against the logged-on user, malware, an administrator, reparse races, filesystem rollback, or process-memory inspection.

## Safe recovery sequence (laboratory)

1. On a disposable Windows test account and private temporary directory, invoke provision(path,cabinet,workstation) once. Never use actual patient media or a production key.
2. Verify unlock works under the same user/profile and explicit cabinet/workstation; do not print the key.
3. backup_sealed makes an exclusive destination containing only ciphertext and binding metadata; test integrity and physically separate backup custody in a future authorized phase. Copying this file alone is NOT a disaster-recovery plan.
4. If the primary envelope is lost but the original DPAPI user profile/master keys remain accessible, restore_same_user performs a non-overwriting import only after successful native unprotect. A revoked destination remains blocked.
5. Missing/partial/corrupted envelope, wrong scope, inaccessible Windows profile, DPAPI failure, tombstone, and recovery collision: explicit refusal; NO silent key generation, missing-record repair, decryption fallback, cleartext export, or clinical capture.
6. Key rotation, removal of old versions, device/account replacement, backup restore on a different Windows account, and destructive revocation remain HUMAN_GATE_REQUIRED until a new authenticated/key-versioned spool and recovery contract is proven.

## Verification

Run: python -m unittest discover -s tools/imaging_gateway/tests -v

CI: existing LOT06 synthetic workflow runs Ubuntu plus Windows. Portable parser/contract negatives run on Linux and Windows; native CryptProtectData/CryptUnprotectData roundtrip, process restart, same-user sealed backup/restore, tamper, scope mismatch, local revocation, crash-partial record and DPAPI denial execute only on Windows. This is hosted-runner evidence, never physical-clinic proof.

Scope locks: LOT04/05 untouched, no database schema, backend, frontend/mobile, driver, Windows service, master merge, Vercel, clinical activation or patient data. No clinical/equipment certification. LOT06-B2 server-ledger/device-auth gate remains independently blocked.

Adversarial correction (06-H candidate): sealed-record reads compare metadata before/after the bounded read, use O_NOFOLLOW when the platform offers it, and reduce raw OS failures to fixed codes. A second revocation check follows DPAPI unwrap. Race-free Windows reparse protection still requires the physical NTFS and installer gate; it is NOT proven by this mitigation.
