# V1.5-05.7A — Product trust-root security gate (DRAFT / NO-GO)

Date: 2026-11-05. Canonical authority: Notion V1.5 roadmap, LOT05; product contract `docs/quality/V15_05_SQL_MIGRATION_CONTRACT.md`. This is a **security decision and acceptance contract**, not implementation or authorization to import clinical data.

## Current evidence / boundary
- Preparation 05.1–05.6 is merged (#890). J9 candidate #984 is DRAFT, FAKE-only, not merged; source HEAD observed `3756de8841f1f5234616e650d1c7afad598fefd5`.
- J9 proves a real ephemeral Windows SCM LocalService service and RSA signature checks in isolated tests, including cross-SID ACL denial, JWT checks and clinical fail-closed.
- J9 explicitly does **not** attest a Digital Crown product installer, independent issuer root, authenticated production IPC, anti-rollback or full DB/WAL/SHM/media recovery. Admin/SYSTEM of the CI runner controls the RSA private key, public pin and synthetic JWT secret.
- Keep SQL migration `import_permitted=false` and `full_schema_certified=false`. **Guided Restore** (`GuidedRestoreService.request_apply` / `GuidedRestoreWorker.run`) is an existing separate backup/restore flow with its own owner, cabinet runtime and recovery guards; it is **not** LOT05 SQL importer. Preserve its existing synthetic integration, rollback and permission tests. Do not introduce a blanket-deny into those entrypoints to implement LOT05.7A.

## 05.7A minimal architecture decision
1. **Issuer vs requester:** The desktop UI, JWT-bearing requester and clinic DB must never be able to mint migration authorization tickets or replace the trusted issuer pin. A JWT establishes user identity, **not** restore authorization.
2. **Provisioning:** Define a signed installer/provisioning manifest that binds publisher identity, service binary hash/version, service SID, allowed operation audience, verifier key fingerprint and policy version. Provision under Windows service-controlled ACLs; attest the manifest and executable at runtime. An administrator with unrestricted host control is **not** a cryptographic trust boundary: explicitly document the threat model, protect key material using an independently controlled signing authority, and fail closed if independence cannot be established.
3. **Authenticated IPC:** Use a named pipe or equivalent local authenticated channel with peer token/service identity validation and strict request schema. No unauthenticated local JSON, temp files or caller-writable outbox may authorize an operation.
4. **Ticket binding:** Signature must cover operation, tenant, exact source/target hashes, approved mapping/dry-run digest, target backup manifest, expiry, nonce, issuer key ID, installed service identity and consent record. Reject wrong audience, tenant, operation, version, signature, replay, expiry and key rotation mismatch.
5. **Replay/rollback:** Persist a monotonic, integrity-protected consume ledger outside any rollback-able target DB snapshot. Define fail-closed behavior if ledger unavailable or older than restored backup.
6. **Clinical activation separation:** Even a valid ticket cannot enable import until 05.7B+ full data integrity, atomic backup/restore, consent and human/physical gates pass. Maintain a separate explicit owner GO decision.

## Required FUE-G05.7A adversarial matrix (all exact candidate SHA)
- No JWT / forged JWT / wrong role / wrong tenant / revoked operator -> DENY.
- Requester-generated signature / swapped public pin / replaced binary / wrong Service SID / wrong IPC peer -> DENY.
- Altered mapping, source hash, destination hash, backup manifest, operation, expiry or audience -> DENY.
- Reused ticket after service restart, crash, DB rollback or key rotation -> DENY.
- Unauthorized service or same-account-different-SID cannot read private key or write authoritative outbox -> DENY, with native Windows ACL evidence.
- Valid synthetic request through **installed, attested product service** and authenticated IPC -> observable authorized *no-op* only; clinical apply still DENY.
- Windows + Linux where applicable; executed test counts, logs, negative assertions, exact SHA, artifacts and risk-based FUE-0 / FUE-I / FUE-G evidence (no mandatory independent A/B review). No synthetic success is physical/clinical certification.

## Decision / stop conditions
**05.7A PRODUCT GATE = OPEN.** A successful J9 FAKE-only CI cannot close it. Do not merge a runtime change, install service, alter clinical DB, enable import, or deploy without a separate FUE-validated implementation and explicit owner approval. Next deliverable: issuer/provisioning trust-boundary decision, followed by a narrowly scoped implementation PR and FUE evidence. An independent **issuer** is a technical key-ownership requirement, not an external reviewer requirement. Physical workstation/installer verification belongs to LOT10.

## 2026-11-05 corrective FUE finding — Guided Restore regression
- PR #1214 initial blanket-deny on Guided Restore caused **4 failed / 12 passed** tests in Settings Guided Restore AFTER (`#42056906137`); the affected existing synthetic owner-dispatch, DB+media restore and rollback tests are valid invariants, not tests to rewrite.
- Both unrelated Guided Restore runtime files were restored bit-for-bit to `master` on the PR branch; invalid blanket-deny AST test removed. These changes restore prior behavior but do **not** establish product issuer, signed installer manifest, authenticated IPC or replay-resistant ledger.
- Required verification: on final PR HEAD, Settings Guided Restore AFTER targeted tests and actual AFTER evidence where applicable; FUE/RPG-C/X/F for LOT05 trust-root security remains **OPEN** until implemented. Do not interpret a green Guided Restore suite as 05.7A product certification.
