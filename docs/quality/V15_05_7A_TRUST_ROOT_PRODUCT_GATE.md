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

## 2026-11-05 — 05.7A-A verifier-only implementation, FUE synthetic scope

**Implemented, not product-integrated:** `backend/services/legacy_migration_trust_root_v15.py` contains an Ed25519 public-key verifier for operation `SYNTHETIC_NOOP` only; there is no signing key, private signer, installed product issuer, UI/API route, SQL importer call, job launch or live activation in the module. The result is `SyntheticNoopReceipt(clinical_import_permitted=False)`. Existing Guided Restore files retain the exact master blobs; previous restorative/rollback behavior must remain green.

- Envelope: strict canonical JSON of exactly `body` and `signature`; no duplicate keys, unknown body fields, oversized payloads, noncanonical encodings or boolean-as-integer claims.
- Signature: Ed25519, domain-separated bytes, pinned SHA-256 fingerprint checked against a **separately provided** verification key. This verifies the supplied pin **against itself**, not independent installer authenticity; product caller cannot provide or replace the pin.
- Bound claims: operation/audience, tenant, source+target+mapping+dry-run+backup+consent SHA-256, installer manifest digest, issuer key ID, policy version, installed service identity and nonce. Validity window maximum 120 seconds.
- Replay: an atomic ledger is REQUIRED; denied when missing, unavailable or already consumed. FUE ledger is **in-memory fake only**, with shared-state duplicate assertion. It does not prove durable rollback/crash behavior.
- FUE suite `backend/tests/test_legacy_sql_057a_trust_root_fue.py`: 38 executed cases locally on an isolated fixture, 38 PASS; cryptographic fake private keys generated only in tests. GitHub Actions workflow `.github/workflows/v15-05-7a-trust-root-fue.yml` runs the same suite on Ubuntu and Windows. Exact-head CI required before calling this verifier-only substep green.
- FUE-0: N/A (no UI or interactive journey). FUE-I product: OPEN (no installed service/IPC/JWT attestation). FUE-G partial: only signature, binding, expiry and in-memory replay denial. RPG-C: exercised via pytest; RPG-X and RPG-F installation/restart/anti-rollback: OPEN.

**Remaining hard stop:** The authority object is accepted as a test parameter, not sourced from an installed signed manifest. An attacker who can replace **both** public key and claimed fingerprint can supply a different authority. Nothing in the verifier alone prevents that. Production needs a separately controlled publisher/issuer root, installer manifest signature and executable/SID attestation, authenticated peer IPC and atomic persistent replay ledger. Fail closed unless every such requirement is proven. User JWT, real clinical data, consent and 05.7B+ backup/rollback certification remain separate NO-GO gates.

**No product PASS / no merge / no deploy / no clinical import** on this isolated proof.

## 2026-11-05 — 05.7A-B Windows-native SCM/IPC FUE (pending exact-HEAD evidence)

Scope: `backend/tests/fixtures/lot05_7a_b_windows_scm_pipe_noop.cs` and `backend/tests/fixtures/lot05_7a_b_windows_scm_pipe_probe.ps1` are **CI-only ephemeral Windows Service Control Manager fixtures**, not installed Digital Crown product services. The new Windows job in `.github/workflows/v15-05-7a-trust-root-fue.yml` checks the actual service process running as LocalService with an unrestricted `NT SERVICE\\<name>` SID in its token, and a Windows named-pipe server that obtains the peer SID using impersonation (`RunAsClient`), never trusting a claimed SID from request text.

The lab restricts pipe access to a service SID and configured caller SID, checks the OS-derived SID against the expected principal, accepts exactly `SYNTHETIC_NOOP_V1`, rejects declared-identity injection and clinical commands, and tests an intentional mismatch between actual OS token and allowed application principal. This isolates SCM and native IPC behavior from J9's file-based job. The lab compiles with the Windows .NET Framework compiler, registers disposable SCM services in GitHub Actions, removes them afterward and asserts cleanup. It handles no PHI, licenses, private signing keys, actual import or existing Guided Restore operations.

**Important limitations:** (1) This CI harness installs temporary test services only; it does not produce a signed Digital Crown installer or independently attest product binary/hash/service identity. (2) It does not integrate or authenticate the Ed25519 ticket to a validated JWT/tenant principal: `SYNTHETIC_NOOP_V1` is merely a transport probe, never an authorization to import. (3) FUE does not demonstrate cross-user account ACL attacks, certified publisher root, trusted manifest, durable replay after power loss/DB rollback, or production install/upgrade. (4) The fixture passes the expected SID from the privileged CI provisioning script; a compromised local administrator is outside the claimed trust boundary and can reconfigure it. (5) On real product installation, the authorized user must be derived from trusted server-side policy; a caller-provided SID remains forbidden.

**State:** 05.7A-B test implementation committed, exact-head native Windows SCM/IPC FUE pending; PRODUCT GATE OPEN. The no-op transport probe is **not** proof that installed product signer authority or clinical migration is trustworthy. No merge, deploy, or clinical import.
