# LOT06-M — HUMAN GATE decision packet v1 (review candidate)

**Date:** 2026-10-15. **State:** PROPOSED — architecture/design gate NOT approved for physical implementation. **Repository:** `hraaaaf/Digital_crown`, PR #851 (DRAFT). **Starting source:** `143b221af2ef53b024ad543b87177007f9040d29`. **Controlling ADR:** `docs/quality/V15_06_M_DURABLE_AUTHORITY_ADR.md` §2–7, §8, §22. This packet clarifies the proposed decision; it does not override the ADR or assert a working witness.

## 1. Recommendation and limits

**Recommend Option D, conditional**: (a) a local encrypted capture coordinator, transactional intent/outbox and HMAC+AEAD journal on the clinic workstation; (b) a **separate, locally administered LAN witness host** in a different administrative/rollback domain; (c) independent encrypted cold backup and recovery evidence with different authorized custodians. The witness is an **authority over accepted transitions**, not a media, patient, diagnosis, or clinical authorization server. No patient identifiers or patient media go to the witness. A random opaque scope can nevertheless remain personal/pseudonymous data when linkable; privacy review required.

**Scope boundary:** Design only in this change. No real SQLite/SQL migration, NTFS writes, Windows service, network endpoint, private signing key provisioning, cloud witness, equipment order, patient access, collector integration, production deployment, master merge or clinical ACK. The user's “Go” follows a proposal for making the HUMAN GATE decision; it is **not evidence** that site topology, key custodians, costs, safety and operating policy have been explicitly approved.

**Single-PC clinics:** they cannot claim independent anti-rollback under a one-computer deployment; offline workstation-only SQLite may support a local outbox but is NOT accepted as an equivalent witness. A centrally administered or hosted witness would be a separate design/privacy/jurisdiction/budget approval, not a silent fallback.

## 2. Architecture / failure domains

```text
Capture workstation (admin A)             Witness appliance / host (admin B)
  encrypted candidate + source              authenticated device enrollment
  J/K HMAC+AES-GCM journal                   atomic monotonic head + immutable op ledger
  durable SQLite outbox/intent               authority epoch / scope / key registry
  NO witness private key                     private signer only here
             |  mutually authenticated LAN challenge / CAS  |
             +--------------------------->------------------+
                           authenticated current head / signed receipt
Independent recovery domain (custodian C, independent of A and B):
  encrypted journal/media snapshots + witness log/epoch snapshots,
  key catalogs, protected high-watermark / append-only audit and drill evidence
```

The three roles A/B/C must be enforceably separate. Two machines sharing the same privileged account, backup administrator, hypervisor/root domain, or editable snapshot repository do **not** independently resist coordinated rollback. A compromised witness signer, compromised administrator B, or simultaneous rollback of witness and recovery high-watermark defeats global freshness claims; record residual risk and escalation to HUMAN GATE, never claim absolute protection.

**Connectivity/availability choice:** LAN-only, without internet dependence, is the preferred *design* for an on-prem clinic; it is **not a validated site topology**. During witness outage or uncertain epoch/head: encrypted staging only where separately authorized; **no new witness decision, local COMMITTED promotion, fresh-sensitive reads or B2 clinical ACK**. Existing clinical access rules require a separate safety/workflow assessment; do not reinterpret a witness receipt as clinician consent.

## 3. Authority state, CAS, freshness and receipts

**Proposed durable witness transaction invariant** (to be implemented and proved separately):
- Identity key: `authority_id, epoch, scope` with one active authenticated enrollment per capture identity; forbidden alias/rebind within epoch.
- For each submitted request, a canonical versioned digest binds `op_id, previous(seq/mac), next(seq+1/mac), manifest_digest, phase, key_ids, authority/epoch/scope`.
- In a **serializable durable transaction** at the witness, compare previous head, reject stale/forked requests, enforce uniqueness of `(authority,epoch,scope,op_id)` and exactly one successor per parent, append an immutable complete decision and update monotonic head. Identical `op_id` + identical canonical bytes replays the *same* decision; changed bytes refuse even after subsequent operations.
- The **complete signed receipt bytes** and corresponding decision/head must be included in the same committed witness transaction, or there must be a separately proven recovery-equivalent durable protocol. If signing occurs within transaction, do not expose its output to callers until a successful durable commit. Signer isolation and durable signing-failure semantics need negative tests.
- Do **not** replace committed state with a bare counter, in-memory lock, success response, timestamp, or a locally supplied head.
- Authenticated latest-head query: the client supplies a fresh unpredictable challenge; witness signs a canonical versioned `authority, epoch, scope, sequence, head, challenge, key_id` response read from its durable state. A signed challenge response authenticates *what the reachable witness said now*; it cannot on its own defeat witness-side rollback/compromise. Independent protected high-watermark, custody and cross-domain restoration checks are mandatory for that threat.
- The read-only Ed25519 laboratory verifier in `signed_witness_receipt_lab.py` is **NOT** an implementation of these requirements. Caller-supplied pin and caller-supplied current head are not external authenticity or freshness evidence; old receipt+old head and two separately signed forks remain counterexamples.

**Ack/state taxonomy:** distinguish `ACK_LOCAL` (staged), `DECIDED` (durably persisted witness outcome), `SIGNED_HISTORICAL_ONLY` (forensic), `COMMITTED_LOCAL` (fully reverified finalization) and later, separately gated, B2 patient/clinician ACK. A time-out, missing witness, bad signature, diverging head, missing legacy key, unknown epoch or ambiguous restore yields `UNKNOWN/QUARANTINE`, **never** auto-success.

## 4. Key custody and incident policy (proposal, not provisioned)

| Secret / public trust root | Proposed owner | Exposure and recovery rule |
| --- | --- | --- |
| Ed25519 witness signing private key | B / independent witness operator | Never copied to capture PC, logs or ordinary backup. Prefer a validated non-exportable signer **only if the exact TPM/HSM/device supports Ed25519 and required transactional interface**; feasibility and cost unverified. No automatic fallback to an exportable signing key. |
| Witness public pin and signer key-id | Enrollment custodian, separately approved channel | Authenticate out-of-band, bind authority/epoch/scope, retain retired public keys for historical verification. Hashing an attacker-selected public key does **not** authenticate its provenance. |
| Clinic journal HMAC and media AEAD keys | A / clinic protected local authority | Independent from witness/backup secrets; rotation keeps previous keys until restore evidence succeeds. Never put patient keys/identifiers on witness. |
| Recovery encryption material / backup metadata | C / recovery custodians | Encrypted, independently controlled, with dual-approval restoration and immutable evidence of prior high-watermark. A backup alone is not proof of recoverability. |

**Signer loss / rotation:** prohibit silent key regeneration with the same authority identity and epoch. Old valid receipts remain historical under previously pinned public keys. A newly approved epoch, new authenticated pin and reconciliation from independently held intact decisions/high-watermark require **two distinct humans**, incident record, revocation/dual-read plan and a tested cross-host restore. If witness, history/high-watermark and recovery material are all unavailable or rolled back, **automatic safe recovery is impossible**: stop, do not rebase to genesis.

**Pending human decisions:** exact hardware/OS/signing capability, distinct named A/B/C custodians, compromise/recovery quorum, budget and maintenance owner, second location/offline media topology, lawful witness metadata handling, revocation/trust-root lifecycle. None is deemed approved by CI or this file.

## 5. Crash/recovery acceptance design (synthetic test objects only until separately authorized)

| Gate | Induced failure or adversary | Expected observable refusal / recovery |
| --- | --- | --- |
| B0 | Before staging/intent | No decision or new ACK, original source retained |
| B1 | Encrypted candidate staged, no intent | Orphan quarantined; no promotion |
| B2 | Durable local outbox; request in flight / no response | Query **same** op_id and payload; UNKNOWN until authenticated decision; no new id |
| B3 | Witness durable commit, response dropped | Query op_id + fresh authenticated head; exactly one durable decision; not a B2 ACK |
| B4 | Witness advanced but local journal/media torn | AUTHORITY_AHEAD; independent verified suffix/media/keys or incident; no invented evidence |
| B5 | Witness down, key lost, or epoch reset | Fail closed; cannot adopt local head |
| B6 | Delayed old signed receipt after later accepted transition | Historical only; no current-head authorization |
| B7 | Restore old local journal + its locally stored head | Compare externally authenticated current head and trusted high-watermark; refuse stale local |
| B8 | Two physical writers propose same parent (including same op-id/different payload) | Exactly one serialized CAS winner; other permanently stale/conflict, identical replay idempotent |
| B9 | Local and witness/backup rolled back or privileged administrator controls both | No unsupported freshness; cross-domain high-watermark must expose mismatch or HARD NO-GO |

Mandatory additional tests: power-loss/process-kill at every flush, commit, signature, reply and local-finalize boundary on declared **real** Windows/NTFS/SSD configurations; network partition/delay/reordering; durable ledger + head + receipt invariant after reboot; device enrollment/revocation, stolen identity and key compromise, dual-operator recovery, cross-host restore with truly independent archival provenance. Distinguish process kill vs physical power removal; synthetic CI cannot claim the latter. Restore must preserve entire authenticated journal and required DC6A/DC6B encrypted media, not just the head.

## 6. HUMAN GATE decision and exit criteria

Design baseline proposed: **D — hybrid separated local coordinator + durable separately administered on-prem witness + independent encrypted recovery domain.** This text is an engineering recommendation, **not a clinical, procurement, physical, or regulatory sign-off**.

Approval checklist (all must be explicit before any physical prototype):
- [ ] Named host/workstation OS and network topology, plus independence analysis of admin, hypervisor, snapshots and power domains
- [ ] Witness persistence/transaction mechanism and concrete real-hardware failure tests approved
- [ ] Real signer implementation, supported Ed25519 key protection, pin enrollment, rotation and escrow/recovery controls agreed
- [ ] Independent archive/high-watermark custody with recovery roles and cross-host restore path agreed
- [ ] Clinic-single-PC and witness-outage operating policy, including clinician safety impacts, approved
- [ ] Opaque metadata minimization/privacy assessment and retention, incident and escalation owners named
- [ ] Cost/site permissions, synthetic-only pilot limits and permitted device/storage/network changes approved
- [ ] Two genuinely independent reviewers assigned for later implementation/recovery evaluation

**Evidence gate after any authorized prototype:** exact code SHA + Windows/Linux CI/coverage; *actual* durable CAS/idempotency logs from two independent writers; powered-off/restarted state inspection; B0–B9 and backup/restore proof; independent key custody verification; separate security and reliability reviews on same SHA with clean confirmation. Every new SHA resets the review evidence. **Strict >9.5 for both axes is not achieved now.**

**Current status: LOT06-M OPEN, HUMAN GATE PENDING, PR #851 DRAFT/unmerged, clinical NO-GO.** No deployment, service, patient write or procurement is authorized by this packet.