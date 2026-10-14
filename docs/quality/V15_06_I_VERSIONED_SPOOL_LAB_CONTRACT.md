# LOT06-I — Key-versioned encrypted spool and reversible candidate rewrap (LAB ONLY)

Status: OPEN. PR #851, isolated LOT06 branch. No patient or server workflow, no hardware, key custody, clinical or recovery certification.

## Why this exists

The live LOT06-A spool ciphertext is \`DC6A || nonce[12] || AES-256-GCM(ciphertext+tag)\`, authenticated using \`DC06A|cabinet|workstation|dedup_identity\`; it has **no key identifier**. Changing the single \`DC_IMAGING_SPOOL_KEY_HEX\` before draining that backlog would strand pending encrypted captures. 06-H appropriately refuses live rotation. This isolated proof-of-concept permits examination of a versioned envelope without touching the existing collector.

## Proposed on-wire v2 (NOT active)

\`DC6B || key_id[16 opaque bytes] || nonce[12] || AES-256-GCM(payload, tag[16])\`. The key identifier is a random opaque 128-bit **identifier**, not key material, and must never be reused for different key material. The AAD is \`DC06I|cabinet|workstation|capture_identity|DC6B+key_id\`; it protects both the scope and key-version header. A known SHA-256 of original plaintext is verified separately. A record cannot be decrypted by guessing a key, selecting the newest key, or treating a v2 envelope as v1. Keyring maps identifiers to 32-byte keys, injected explicitly by the calling synthetic test. The versioned format has 48 bytes overhead; input remains bounded to 50 MiB.

The contract intentionally does **not** use a literal key digest/fingerprint as the key ID: key IDs should be random independently assigned metadata, with a future authenticated issuer and provenance. The existing capture-identity HMAC uses the legacy key: rotating the live dedup key separately requires its own identity-continuity plan.

## Lab-only operation

\`encode_v2\`, \`decode_v2\`, \`decode_legacy_v1\`, and \`rewrap_legacy_v1\` operate strictly on *bytes in process memory*. Rewrap explicitly checks the legacy v1 AAD + authentication tag and digest with the OLD key, creates a new candidate using an explicitly chosen NEW key ID, then decrypts and verifies the candidate before returning it. The legacy ciphertext is not mutated. There are no filesystem operations, overwrite/delete, SQLite writes, backend calls, patient identifiers, or changes to HotFolder/CLI/preflight.

Synthetic negatives cover unknown keys, wrong key length, modified key-ID headers, wrong cabinet/post/capture binding, SHA mismatch, truncation, mutated nonce/tag/ciphertext, downgrade attempts, missing target key, verification failure, separate version keys, nondeterministic nonces, and retained originals. Assertions run on GitHub-hosted Ubuntu/Windows.

## Blocked transition to production

Before adopting v2, **new human approvals / independent work** must establish: stable device identity; provisioned Windows service account with DPAPI profile and NTFS ACL gate; recovery from loss of profile/workstation, offline escrow and retention; version identifier authority and persistence across reboot; durable multi-key retention and secure decommissioning; transactional copy-on-write migration with an audit/manifest/journal, fsync, crash recovery and validated rollback; atomic association of version with spool SQLite row and integrity recheck; concurrent readers/processes handling; staged human authorization and actual patient/asset ingestion server gate 06-B2; field tests on NTFS/antivirus and physical acquisition devices.

There is deliberately no CLI switch, no existing ciphertext modified, no SQL migration, no master merge, no LOT04/05, no Vercel or hardware installation. The 06-G Windows preflight remains BLOCKED. LOT06 remains NO-GO clinical regardless of laboratory green CI.

Reproducible synthetic suite: \`python -m unittest discover -s tools/imaging_gateway/tests -v\`; require exact SHA Linux/Windows logs and two internal adversarial perspectives, with no claim of independent external convergence.
