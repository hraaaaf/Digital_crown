# V1.5 LOT06-M — ADR: durable monotonic authority and crash-safe recovery

Date: 2026-10-14. Status: **LAB / architectural recommendation only**. Input HEAD: `5a38b9ba63935e135da3749088ea8066e929332f`, PR #851 DRAFT. LOT06 **OPEN / clinical NO-GO**. This ADR does not authorize a service, TPM, disk/spool write, patient access, SQL migration, merge or deployment.

## 1. Existing contracts, inspected at input HEAD

- `migration_lab.py`: immutable `Snapshot`, SOURCE/PREPARED/VERIFIED/COMMITTED/ROLLED_BACK; `begin/prepare/verify/commit/read_active/restart/rollback/exercise`. A COMMITTED marker is memory-only; `operator_confirmed` is a test boolean, not real authorization. DC6A source and its old key must survive.
- `journal_lab.py`: `Record(sequence, previous_mac, snapshot, mac)`, `Journal`, caller-owned `TrustedAnchor(sequence, mac)`; `verify_chain` checks the HMAC chain, media AEAD and **exact** head equality. No physical freshness or anchored timestamp; 256-record lab limit.
- `fork_lab.py`: `Draft` and `VolatileAuthority.compare_and_swap/recover`. CAS is sequential in-process. Recreating authority from an old genesis defeats rollback detection; no multiprocess CAS.
- The collector's historical HMAC-derived capture identity, persistent operator consent, device identity, patient link and clinical B2 idempotent receipt are unsolved. Never put patient identifiers into witness metadata at this stage.

Threats: two writers sharing an old head, tampered journal, local administrator restoring both local files, separately compromised witness, stolen HMAC key, power cut at every step, network outage, lost legacy key, and backup restore to replacement Windows device. An HMAC proves authenticity relative to its key, **not freshness** if journal and anchor roll back together.

## 2. Architecture comparison

| Option | Anti-rollback, forks, CAS/atomicity | Offline, backup/restore, compromised keys | Privileges, Windows, operations |
|---|---|---|---|
| A. Independent **on-prem authority service** on separate host | Durable serial CAS possible, stops rollback of capture PC alone; authority backup/reset or admin compromise still defeats it. No cross-host transaction | No new COMMIT during authority outage; authority recovery/epoch/escrow require separate trust | mTLS, distinct admin and hardened service, extra device/network; acceptable candidate but insufficient alone |
| B. **Local transactional SQLite** with log and head in same DB | SQL transaction/CAS can reject local concurrent writers, but restoring whole DB + spool rewinds both; no independent anti-rollback | Strong local availability, easy local backups; DPAPI CurrentUser does not solve lost profile/keys | Simpler Windows integration/cost; **REJECT as sole anti-rollback authority**, retain only as coordinator/outbox |
| C. **Hardware monotonic counter** (TPM/appropriate device) | Possible protected monotonic primitive, but NV lifecycle, reset, counter CAS, forks and write endurance not established | Potential offline operation; motherboard replacement, escrow and cross-device restoration difficult | Needs exact Windows/TPM vendor feasibility/driver tests; **research option**, not assumed proven |
| D. **Hybrid on-prem**: transactional local coordinator + separately administered durable witness | Witness atomically CASes (epoch, opaque scope, sequence, head MAC/event digest), returns verifiable durable receipt; local outbox makes interruptions recoverable by inspection. **No cross-domain atomic commit claimed** | Local encrypted staging offline, **no promotion/clinical ACK** offline. Independent witness constrains restored local backup, unless witness itself rolled back. Keys/backups separated | Highest cost/complexity, explicit trust/admin/network failure domain; **CONDITIONALLY RECOMMENDED** pending HUMAN GATE |

Decision: **D as a candidate design**, not an implemented/clinically approved solution. Single-PC clinics lacking an independent witness remain NO-GO for a strong anti-rollback claim; do not silently degrade to B. Keep patient media on-prem. Witness would contain only random opaque scope, epoch, monotonic head and signed/authenticated receipt; even pseudonymous metadata need a privacy review. Cloud witness or another installed host requires human authorization.

## 3. Target protocol / invariants (not implemented)

Each operation binds `protocol_version, authority_id, authority_epoch, random_scope_token, operation_id, expected(sequence,mac), next(sequence+1,mac), phase, journal_manifest_digest, source/candidate_hash, key_ids`. The capture token must NOT depend on the collector's historical HMAC key or encode a patient ID. Canonical serialization must be specified and versioned. A signed receipt or MAC from an independent authority identity must be authenticated by readers; no credential/secret shared with the collector. An old epoch must never be silently resurrected.

**I1**: one serialized, durable successor per expected witness head, including across processes/hosts. **I2**: idempotent `operation_id`: identical retry returns same decision; same ID and other payload refuses. **I3**: `ACK_AUTHORITY` only after witness durability, vs distinct `ACK_LOCAL`; neither is a B2 clinical receipt. Lost reply means UNKNOWN until authenticated query; no duplicate operation ID. **I4**: only VERIFIED candidate with valid source and keys can transition to COMMITTED; rollback advances sequence by a new audited event, never deletes a suffix. **I5**: independent roles, keys, domains, escrow and tested restoration. **I6**: unverified epoch, unavailable witness or conflicting witness state => no new COMMITTED/media promotion/patient ACK.

Planned write order: (1) authenticated witness head, source+key+scope check; (2) stage new *encrypted* candidate copy and verify AEAD/digest, prove Windows file+metadata flush; (3) durable local coordinator intent/outbox `PENDING_AUTHORITY` with same `operation_id`; (4) witness validates, serializes and persists CAS+idempotency ledger+decision and **then** returns signed receipt; (5) local journal/receipt finalize transaction and media reread; (6) only after confirming current witness + local chain can phase COMMITTED become eligible for a future reader. Patient association requires a **separate** LOT06-B2 device/clinician/patient/idempotency/atomic-ACK gate. No upload authority follows from this receipt.

A correct architecture CANNOT claim atomicity across SQLite, NTFS and the witness. Lost local intent or candidate **after witness CAS** can strand an operation; the witness must retain a queryable authenticated decision keyed by `operation_id`, and recovery must require matching data/copies. No automatic success on timeout or reconstruction from counter alone. Local transaction implementation must prove Windows VFS/NTFS/SSD power-loss semantics in targeted configurations.

## 4. Crash/recovery classification (deny by default)

| Observation | Required classification / behavior |
|---|---|
| Current authenticated epoch/head equals fully HMAC+AEAD-verified journal and required media | `VERIFIED_MATCH`; read eligibility only by actual migration phase and independent access policy |
| Candidate or intent local, witness still old and undecided | `LOCAL_PENDING`; keep legacy active; replay same op_id only after authenticated head and pending decision inspection |
| Journal/local ahead of witness | `LOCAL_AHEAD`; quarantine; **never** advance witness from local assertions |
| Witness ahead, journal/receipt/media missing | `AUTHORITY_AHEAD`; quarantine; restore from authenticated witness decision + independent archived journal/media; otherwise human incident |
| Equal sequence, different MAC, another accepted branch | `HEAD_MISMATCH/FORK_CONFLICT`; preserve evidence, block; never choose higher timestamp/last writer |
| Witness absent, wrong epoch, unverified or reset | `AUTHORITY_UNKNOWN/EPOCH_CONFLICT`; block all new commitment/ACK |
| Invalid HMAC/AEAD, missing DC6A or key | `INTEGRITY_OR_KEY_FAILURE`; quarantine, no silent downgrade |
| Old backup with journal+old anchor still internally valid, independent witness newer | `BACKUP_ROLLBACK`; block, recover complete authorized suffix to current head |
| Witness receipt durable but local completion interrupted | `DECIDED_NOT_FINALIZED`; same-op idempotent recheck and verify blobs before any finalize |
| Same op_id claimed with two payloads | `IDEMPOTENCY_CONFLICT`; block and audit |

Recovery order: freeze authors/unsafe readers; authenticate current independent witness `authority_id/epoch/scope/head`; inspect its immutable decisions; verify local J/K HMAC **before** AEAD; verify source/candidate bytes, keys, operations and received signatures; **classify without mutation**. Unclassified or ambiguous state => quarantine. Never `reset authority`, `adopt local`, infer a clinical ACK or replay an old genesis.

Authorized reconciliation (future, not LAB): incident ticket and minimized evidence; immutable copy first; compare two independent backups and witness log; two genuinely distinct authorized roles with signed approval; recover missing canonical data only to the current witness head or append an audited *forward* compensating event/new approved epoch. No decrement or deletion. If witness + history or keys are both compromised/lost, **no safe automatic reconciliation exists**; exceptional HUMAN GATE required. A restored local state does not independently prove chronology.

## 5. Failure-domain and operational policy

- Backups must preserve encrypted DC6A/DC6B media, all chain records/receipts, local intents, independent witness decisions/epoch, versioned key catalogs and escrow. Backup success != restore proof; test isolated cross-host restore **against an uncompromised non-restored witness**.
- Separate witness/admin, capture-agent, key escrow, recovery approvers and clinical permissions. Examine common administrator and ransomware trust boundaries: two hosts administered by one fully privileged actor may still be one effective rollback domain.
- Rotate HMAC, media and witness identities with versioned manifests, dual-read transition and old-key retention until audited restore succeeds. DPAPI CurrentUser is not disaster-recovery escrow. No key destruction or physical migration within 06-M.
- Offline: local encrypted staging MAY continue within existing authorized collector behavior, but no witness CAS, promotion to new COMMITTED or B2 receipt. Already committed local reads without fresh witness cannot assert current high-watermark; choose fail-closed when freshness matters.
- No authorizing a Windows service, storage mutation, network witness or TPM without human decision; assess real costs, patching, outage support, recovery runbooks and site topology.

## 6. Proof matrix, decision gate, exclusions

**LAB experiment only**: `reconciliation_lab.py` classifies caller-supplied (thus **not authenticated**) anchor, epoch and J/K journal; negative tests for missing authority, old snapshot, head mismatch, key failure, ahead/behind and epoch conflict. It never writes, repairs or produces an ACK. Restoring **both** old journal and old caller-provided anchor will still give `VERIFIED_MATCH`: this is a deliberate negative proof, not security success.

**Before HUMAN GATE for physical prototype**: protocol/epoch/signature/CAS specification; threat model including malicious admin and split brain; separate on-prem failure domains and operating-cost choice; mTLS/device registration, privacy of witness metadata, key escrow and rotation design; independent operator approvals; Windows VFS/FS durability plan; ineligibility of one-machine clinics made explicit. Approval needed before implementing/installing service, disk writes, DB, TPM or equipment.

**Before clinical GO**: actual Windows NTFS/SSD power-cut tests at every write boundary, process/network races, Linux/Windows unit CI at exact SHA, cross-machine backup/restore, lost ACK and duplicate idempotence under real durable CAS, crypto compromise/revocation drills, manufacturer equipment & driver integration, B2 patient/device/human confirmation + atomic clinical ACK, independent expert security review and qualified clinical risk acceptance. CI of this ADR does not meet these gates.

**Forbidden/out of scope**: active collector/CLI, LOT04/05, backend/mobile, SQL, patient data, real spool, service/driver/hardware, Vercel/master, clinical activation.

## 7. Technical source scope

- Source code at input HEAD: `tools/imaging_gateway/{migration_lab,journal_lab,fork_lab}.py` and J/K/L quality contracts.
- SQLite official: https://www.sqlite.org/atomiccommit.html and https://www.sqlite.org/pragma.html — transaction durability relies on VFS/OS/device assumptions, not independent rollback protection. WAL `synchronous=FULL` is a candidate to verify, not certified on target hardware.
- Microsoft FlushFileBuffers: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers — flushing one file buffer does not establish multi-file atomic commit.
- TPM vendor/hardware behavior and counter endurance unverified for Digital Crown. No claim of validation or applicable standard/certification.

**Residual blockers**: independent trust domain and reliable monotonic CAS not implemented, cross-store crash recovery unproved, operating availability offline, escrow/rotation, key compromise, Windows physical tests, legacy capture identity, B2 and dental devices. **Recommended architecture = D, conditional. Clinical status = NO-GO.**

## 8. 06-M corrective specification after quality gate failure (review B = 7.9/10)

**Gate correction**: CI green on prior SHA `3aced804...` did not validate the architecture; reliability score 7.9/10 is below the strict 8.0/10 minimum. This section stays within **LOT06-M**. It does not make a durability or clinical claim.

### 8.1 Authority-side atomic decision record — mandatory physical contract

The authority (not the collector) must make `CAS(old_epoch, scope, expected_sequence, expected_mac) + append immutable decision + operation_id/complete request digest uniqueness + receipt` **one durable, serializable transaction**. A process must never return a success receipt before this *same* transaction is durably committed. An incomplete transaction cannot expose an advanced head without the corresponding durable decision. Head, decision ledger and receipt must be covered by the same rollback-protected authority failure domain; a signed receipt alone is NOT a freshness proof. Uniqueness is (`authority_id, epoch, scope, operation_id`); reuse with a different canonical byte-for-byte intent **conflicts**, even when the head has since advanced. Canonical request digest binds full proposal, candidate manifest and expected/next head. No operation-id reuse after epoch rotation without an audited epoch transition.

No safe proof is possible from a *bare* counter increment without the matching manifest/decision and recoverable encrypted media. The authority returns `DECIDED` only with the receipt; `UNKNOWN` on failed query or partition; `CONFLICT` on reused identifier with changed body; `STALE` when competing CAS won; `NOT_SEEN` is not definitive while a delayed request may still arrive. After timeout, query by the *same* operation ID **and same payload**; do not generate a new ID or promote media because a network timeout elapsed. Retrying the same ID must be idempotent, including after receipt loss and later unrelated accepted operations. A receipt about a prior decision does not establish the **current** witness head.

Trust-domain non-claims: in-memory `VolatileDecisionWitness` uses 06-L `VolatileAuthority` + an ordinary Python dict, sequentially. It models decision and receipt together **logically**, not an OS-atomic operation or stable storage. It holds prototype keys and is resettable; in production the authority must not inherit such unrestricted collector key/material privileges.

### 8.2 Crash boundary ledger (no cross-store atomicity)

| Boundary | Authority decision | Local evidence | Recovery rule |
|---|---|---|---|
| B0 before staging | old head | old verified journal | remain old; no new acknowledgment |
| B1 candidate staged, no local intent | old head | orphan encrypted candidate | quarantine orphan; legacy remains active |
| B2 intent/outbox durable, no decision known | old or racing | local intent, source and candidate | query immutable `op_id`; retry same body only; never switch to a new id on ambiguous timeout |
| B3 witness transaction durably commits, ACK lost | advanced, decision exists | older local journal | query same `op_id`, verify receipt and current head; `DECIDED_NOT_FINALIZED`, **not a clinical ACK** |
| B4 witness advanced, local transaction/receipt torn | advanced | journal/intent stale or incomplete | `AUTHORITY_AHEAD`; require full independently retained authenticated chain+media/keys and human reconciliation |
| B5 finalized local chain, witness inaccessible/reset | unknown trust | apparently valid committed local | quarantine; no fresh promotion, B2 ACK, or unsupported freshness |
| B6 another decision advances witness after first | newer head | old valid receipt | old receipt remains queryable, but is **not** permission to assume current head |
| B7 backup restores journal + locally stored anchor | witness should be newer | internally authentic but stale journal | detect only with independent uncompromised witness; otherwise global rollback remains undetectable |

**Recovery proof bundle** (required *before* any future human-authorized physical reconstruction): authenticated independent witness identity/epoch/current head plus *all* immutable decisions from local prefix to head; independent archived full 06-K chain incl. **every** missing record; authenticated DC6A + DC6B ciphertext and required old/new keys; matching cabinet/station/capture opaque scope; prefix equality vs local surviving journal; stable operation_id and receipts per transition; documented backup provenance and restore test; explicit reconciliation incident, distinct approvers and preservation of forensic copies. In the LAB, even a completely HMAC+AEAD-verified caller-supplied archive returns **CHAIN_VALID_PROVENANCE_UNVERIFIED_HUMAN_GATE**, **not RECOVERED**. Genuine independence/provenance of archive custody, authority identity and epochs must be established by a separate real-world security and restore test, not by this classifier. Media or key missing, forked prefix, missing witness decision, different epoch, witness itself rolled back or compromised = hard block, incident escalation, no automated key rotation/rollback/reset or clinical use.

No automatic solution exists for witness-ahead when the sole candidate/journal copy is lost. If the witness and its decision ledger are lost/rolled back together, the source of monotonic truth is lost; an exceptional independently verified new-epoch recovery plan and HUMAN GATE are necessary. **Availability is sacrificed rather than manufacturing a history.**

### 8.3 Model evidence and limitation

`tools/imaging_gateway/witness_recovery_lab.py` exercises identical-op replay, conflicting op_id payload, competing forks, uncertain/lost reply, old receipts after later decisions, archive completeness, prefix mismatch, missing decision, integrity fault, incorrect epoch and whole-authority reset. It returns only non-authorizing classification codes. The full local/archive evidence remains memory-only and the witness is re-creatable; no physical CAS, durable receipt, cryptographic witness identity, fsync, Windows ACL, independent archival provenance, dual-control approval, or active collector integration is proven. A malicious caller can construct fake witness objects; do not reuse these classes in production.

**Evidence rule**: require exact-HEAD Windows/Linux synthetic CI; two INTERNAL critical reviews with at least 8.0/10 each **and zero unresolved material BLOCKER/MAJOR**, plus an additional confirmation pass. Scores never override findings; no claim of independent convergence from same-assistant reviews. The future physical authority requires a separate human design/topology/escrow decision and power-loss tests. LOT06 clinical status stays **NO-GO**.

**Adversarial correction after first 06-M corrective commit**: simulated receipts bind authority_id and opaque scope explicitly, malformed J/K manifests map to fixed refusal codes, and archive classification never calls a caller-provided chain independently proven. These changes preserve the deliberate lack of durable trust and cannot substitute for signed authority receipts or an independent restore drill.

## 9. 06-M adversarial findings 6.6/6.3 corrected in LAB (2026-10-14)

The strict [A security 6.6](https://github.com/hraaaaf/Digital_crown/pull/851#issuecomment-6179728910) and [B reliability 6.3](https://github.com/hraaaaf/Digital_crown/pull/851#issuecomment-6179746004) reviews superseded earlier internal 8.2/8.2 scores on the previous SHA. Corrections are scoped to synthetic code and CI; NEVER reuse this as a durable-witness approval.

- **SEC-A1 / REL-B2**: receipt ledger must reconcile *the entire witness journal* including equal-head, not just missing suffixes. Match 1 immutable decision per transition, stable unique op_id, before/after, authority_id/epoch/opaque_scope, canonical request digest over archived record chain. Missing/corrupt entries => refusal even if local journal and head match. A SHA digest remains untrusted without an authenticated independent authority.
- **SEC-A2**: canonical domain-separated v2 request digest now covers authority_id + epoch + scope + operation_id as well as expected/next heads and full journal/manifest. Different witnesses/epochs/scopes/ops cannot silently reuse a synthetic proof; physical implementation must *sign* and externally authenticate the envelope, with persistent collision-resistant ledger IDs.
- **REL-B1**: replace old independent Python assignments (head first, receipt later) with a *copy-on-write immutable state* holding history, monotonic head and decision receipts, installed once per logical commit. Serialise LAB contenders using a Python lock. Failpoints BEFORE_INSTALL and AFTER_INSTALL model complete rejection or complete decision despite lost reply. This is NOT cross-process/NTFS/SQLite/SSD atomicity or a real crash experiment.
- **SEC-A3 / REL-B3**: only classify local-ahead/authority-ahead after local HMAC + AEAD verification; distinguish lost local evidence, corrupt local history and a verified stale local prefix. All results remain non-authorizing.
- **REL-B4**: add synthetic tests for before/after state-swap crash, concurrent competing writers, ledger corruption, all receipt fields, domain separation, multi-event missing decisions and missing local evidence; CI coverage remains no substitute for physical interruption.
- **Known hard boundary**: all witness state, keys and receipt evidence are still caller-owned/in-process. Recreating a prior epoch/head with an old full journal still yields a coherent old local state. Actual anti-rollback requires independent separately administered CAS, custody/provenance, signed receipts, fail-safe storage, backup and human approval. LOT06 and patient workflow stay NO-GO.

Success criteria for this correction: exact HEAD test logs on Windows/Linux, 2 new scoped severe perspectives with no residual LAB BLOCKER/MAJOR, additional same-HEAD internal confirmation, Notion POST; independent external review and physical HUMAN GATE remain later.

## 10. Second forensic replay corrective LAB invariants

Prior same-head replay reports [A 7.0](https://github.com/hraaaaf/Digital_crown/pull/851#issuecomment-6180590482) and [B 6.8](https://github.com/hraaaaf/Digital_crown/pull/851#issuecomment-6180600359) identify 3 DISTINCT MAJOR (same-capture alias enrollment, unaudited observe(), quadratic prefix hashing) plus lost-reply race MINOR. New VolatileEnrollmentRegistry is a shared VOLATILE capture->authority/epoch/scope registry; refuses a second instance, scope/authority alias and epoch rebind within that shared namespace. A new registry can bypass it: not a durable global enrollment service. observe now refuses a missing/corrupt ledger. Canonical v3 request digest binds one new record with old/new HMAC heads and identity/epoch/scope/op; accept validates full chain, replay validates accepted exact prefix; this makes ledger-manifest visits linear rather than quadratic, but full ciphertext verification and physical endurance are not proven. lost_reply uses one coherent state snapshot (UNKNOWN is safe for a concurrently accepted operation). Negative tests cover re-enrollment and its separate-registry counterexample, observe on torn ledger, altered historical prefix replay, race, and bounded manifest visits after sixteen synthetic decisions. Actual cross-admin witness, physical crash, big-media latency, custody, escrow, Windows service and clinical ACK remain strictly NO-GO.

## 11. Strict quality loop: new regression proofs and bounded fail-closed LAB work

The previous same-SHA forensic A=7.0/B=6.8 audit exposed three MAJOR: nonce-dependent ciphertext source_sha256 in enrollment scope, late missing-ledger detection in archive decisions, and large unbounded HMAC/AEAD history-verification workloads (as high as 256 x 50 MiB source ciphertext before considering candidates). New tests are synthetic and read-only.

- The SHARED registry now keys by stable logical capture fields (cabinet, workstation, capture identity, clear-content digest), not by the randomized ciphertext source SHA. Per-witness chain scope still retains source_sha256 to authenticate an exact encrypted source. Two valid DC6A encryptions of the SAME capture with different nonce must conflict; a separately constructed registry still bypasses global uniqueness and requires PHYSICAL design approval.
- assess_archive audits witness head+decision ledger BEFORE checking absent media, invalid journal, older prefix or archive missing. Every corrupted-ledger path is fail-closed and cannot disguise witness inconsistency behind an archive error.
- A bounded synthetic per-audit ciphertext workload of 128 MiB refuses new decisions if the cumulative bytes of sources and candidates would exceed it, BEFORE expensive chain verification. Existing state above that bound fails closed on reads. This is deliberately a LAB operating limit, **not** performance certification and **not** a viable long-lived production quota. Long-term architecture needs independently attested incremental checkpoints or authenticated materialized verification indices with invalidation, plus realistic 128/256-event and large-media stress/power-loss experiments. No silent promotion after refusal.
- Four regression tests exercise nonce re-encryption, all early-return archive branches, prospective budget refusal with unchanged head, and legacy over-budget state read refusal. No actual large-media benchmark or real durable anti-rollback is claimed.

ADR historical v2/dict descriptions are superseded by this section and the current v3 immutable-state source. Nothing authorizes a clinical ACK, merge or physical service.

## 12. Quality loop second pass: stable capture ID vs content digest and diagnostic precedence

The shared-registry enrollment key is now stable cabinet/workstation/capture identity (three fields), not source cipher digest **nor clear content digest**, so a fresh valid DC6A envelope carrying another media version of the *same* capture identity cannot enroll a duplicate active witness. The full source ciphertext, content digest and key compatibility remain validated independently by J/K and retained in authenticated per-witness history. In the LAB, identity uniqueness still depends on authorized capture IDs; actual provisioning/attack prevention requires physical human design gate.

The per-audit workload budget is a **distinct deterministic diagnostic**: attempts above 128MiB aggregate retained source+candidate bytes return AUDIT_WORK_BUDGET_EXCEEDED / AUDIT_WORK_BUDGET_REFUSE, separate from ledger tampering, without decrypting/hashing over-budget media. It is intentionally fail-closed, constrains legacy 50MiB media migration/retention and is NOT an acceptable production liveness solution. No claimed performance certification at 128/256 stages. Distinguishing resource refusal from compromised witness ensures trustworthy incident triage.

## 13. Bounded-memory verified snapshot cache with strict invalidation

A forensic post-correction reliability challenge identified repeated HMAC+AEAD scans for every unchanged in-memory head/lookup. The LAB now maintains a non-authoritative verification cache keyed on immutable _State **object identity** and full current key material. New states are installed in ONE authoritative _state assignment; all history/receipt invariants and cipher bytes are verified before cache entry. A failed BEFORE_INSTALL leaves prior cache/state; AFTER_INSTALL can lose the caller reply while the complete cached state and receipt remain installed. Any _State substitution (even an older/shorter or forged history) invalidates the identity cache, forcing complete verification; target-key, legacy-key and HMAC key changes also invalidate. 32 repeated synthetic read/lookup calls require <=34 manifest hashes total, rather than 32 full-chain scans. Three regression tests prove stable cache, tampered state and key change invalidate, and lost response after install does not misreport missing decision.

**Model limitations:** Python dataclass frozen is not a secure process isolation boundary (runtime object.__setattr__, malicious in-process operator, monkeypatch and separate registry can defeat it); process restart loses the verification cache, independent authority freshness and durable key provenance. This is strictly a trust-preserving optimization under ordinary, immutable in-process LAB semantics, not a portable persistent authenticated index. The 128MiB aggregate budget remains a fail-closed LAB cap, not a clinical or practical 50MiB-media service SLO.

## 14. Audit-budget preflight before caller-controlled digest and archive checks

The bounded-work lab rule must apply BEFORE hashing caller-provided proposals. decide/lookup/lost_reply now perform a cheap typed-length preflight ahead of _request_digest; oversized inputs refuse without visiting _manifest. assess_archive and lost_reply also refuse oversized caller local/archived history BEFORE full HMAC/AEAD validation. A corrupted witness ledger still has priority over local status. New tests patch the small LAB byte quota instead of allocating genuine enormous medical images, verify no hash calls for oversized draft, and assert local work refusal before cryptography. These tests do NOT prove real SSD throughput, media-latency thresholds, or any production service budget.

## 15. Idempotent receipt replay without redundant media hashing

When the whole immutable decision ledger and keys are already authenticated, matching one receipt's before/after anchors plus exact accepted historical record tuple suffices to distinguish identical replay from conflicting or changed-prefix payloads. Same-ID decide and lookup, and lost-reply receipt verification, now use an exact immutable request/receipt check without rehashing the ciphertext. New decisions still validate their entire chain and calculate v3 manifest only after CAS checks succeed; replay/unknown lookup never need request SHA. Two new tests patch journal manifest hashing to fail if 50 repeated lookups, retries, or lost-reply classifications attempt unnecessary media digests, and test conflict against altered next head. This is a strictly in-process, memory-only optimization; no claim of durable signatures or independent receipt validation.

## 16. Continuation 2026-10-15 — positive LAB history boundary test, not real-media certification

The exact previous SHA d616440 scored only A=8.9 and B=8.5 on the unmodified strict forensic v1 review. This additional regression constructs all 256 valid synthetic HMAC+AEAD journal entries through the legal state machine, audits the resulting 255 immutable receipt decisions, forces an in-memory cold audit (new _State object) with a manifest-visit bound and checks the next append safely refuses. This closes the **missing positive 256-entry LAB matrix** but cannot resolve the 128MiB aggregate budget versus genuine 50MiB medical images, process/SSD durability, independent enrollment and provenance, key/epoch escrow, or measured real-world 256-record latency. All physical/clinical gates stay NO-GO; do not label lab's finite demonstration production-ready.
