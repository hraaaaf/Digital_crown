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