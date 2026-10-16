# LOT06-N — checkpoint C conditional freshness LAB (synthetic only)

**2026-10-16 | EXPERIMENTAL | DRAFT stacked on PR #899 | NOT PHYSICAL | clinical NO-GO.**
This lab implements a deliberately **volatile** in-process C checkpoint fixture, a signed C anchor and a conditional B/C-head classifier. Its objective is to demonstrate one narrow statement: a full rollback of B's SQLite DB *with the old still-valid B signing key* is detectable **if and only if** an authentic **current** C checkpoint remains intact and independent. The test harness owns BOTH private keys and ALL state. Hence it does not establish actual independent custody, durability, a monotonic hardware counter, WORM, secure transport to C or operational B9 protection.

## Scope and source
- Changes only under `tools/imaging_gateway/checkpoint_c_lab.py`, synthetic tests and CI. No clinical API, application DB, workstation or backend code.
- Bases: [LOT06-M authority ADR](V15_06_M_DURABLE_AUTHORITY_ADR.md), [LOT06-N loopback LAB](V15_06_N_INDEPENDENT_WITNESS_SYNTHETIC.md), and [LOT06-M HUMAN GATE](V15_06_M_HUMAN_GATE_DECISION_PACKET_V1.md).
- Separate PR head, branched from `81d0a6c1fb7cd7761396495d17e5cd4276f7d2b5` (#899). Never infer that #899's old green runs prove this newer head.

## Synthetic protocol assumptions (not design completion)
1. B's `durable_cas_lab.apply` creates an accepted CAS+receipt (signed receipt under TEST B key) on a disposable SQLite file. `SyntheticCheckpointC.anchor(receipt)` verifies authority, epoch, scope, pinned B signer, contiguous `before_seq/before_mac` and exact successor, then signs C checkpoint `(seq,mac,op_id,hash(receipt),hash(previous C checkpoint),witness_pin)`. The full receipt bytes and per-op proof exist only in-memory. An identical replay returns the same signed proof; gap/fork/other key fails closed. The signed historical proof is **NOT a fresh assertion of C state**.
2. `classify_verified_head` requires a **freshly challenged, signed B HEAD envelope** verified under the pinned B public key and a C-signed checkpoint under a different pinned key. It outputs `UNKNOWN_NO_INDEPENDENT_CURRENT_C_LAB` on absent proof; `B_ROLLBACK_DETECTED_LAB` when B sequence is lower; `PENDING_C_ANCHOR_LAB` when B is ahead; `SAME_SEQ_FORK_REFUSED_LAB` when heads differ; otherwise `MATCH_LAB_NOT_GLOBAL_FRESHNESS`, **never DECIDED/COMMITTED, patient ACK or PHYSICAL PASS**.
3. The comparison **assumes** `C_packet` truly represents C's CURRENT trusted high-watermark. The model deliberately does not implement/enforce that assumption. A valid replayed older C checkpoint can match restored older B, demonstrating that **signing C proofs is not sufficient**. A compromised/rolled-back C or common admin domain defeats the claimed independence. Before any use outside LAB, this remains a design BLOCKER.
4. The C fixture is *not* transactionally coordinated with B. A B commit followed by C timeout must remain `PENDING_ANCHOR`; rollback/restore and partial loss require an independently designed production protocol and a separate human decision. No clinical availability claim.

## Test contracts
`test_checkpoint_c_lab.py` tests:
- synthetic signed genesis; sequential proof chain; exact receipt idempotence; replay/gap refuse; wrong C pin, tampered signed checkpoint, wrong B receipt or scope refused;
- missing C or B proof => unknown; B head signed but ahead of C => pending; signed B fork => conflict; old nonce => refuse;
- **B9 negative**: copy B SQLite at sequence 1, commit B seq2, anchor C seq2, restore B from seq1 and retain valid B signer; fresh valid signed B head seq1 is correctly labeled `B_ROLLBACK_DETECTED_LAB` against C seq2;
- **counterexample**: replay old genuine C seq1 proof as well => B seq1 and C seq1 produce `MATCH_LAB_NOT_GLOBAL_FRESHNESS`. This is a negative result, not a safety success. No external WORM / freshness is proven.
- all patients/media/scope are random synthetic data in disposable temporary paths; no service is created or connected to a clinical environment.

## CI classification, physical boundary and exit
- [synthetic C workflow](../../.github/workflows/v15-06n-checkpoint-c-synthetic.yml): Windows + Ubuntu Python 3.11, checkpoint C tests plus original independent B witness tests and LOT06-M SQLite CAS regression on the **same new head**. The run result is authoritative only once retrieved with exact SHA and per-job/test counts.
- REQUIRED for this branch LAB: those three test collections and tests not skipped; green CI is not a physical or architectural approval. Legacy imaging CI may run on PR's temporary merge ref and must not be mislabelled exact-head.
- **LOT10 EXCLUSIVE**: A/B/C real machines, HSM, OS/NTFS/SSD durability, independent-admin reality, C WORM lock & restore, TPM counter, real LAN/power-cut, B0–B9 physical injections, operators, PHYSICAL PASS/NO-GO. Map to LOT10 10.1/10.4/10.7/10.8 and 10.3 where restores overlap. Retain the existing LOT10 13-SP baseline; any additional complexity requires independent LOT10 planning decision. NO pilot hardware in LOT06-N.
- D-STRICT real independence and `current-C` authentic freshness **UNPROVEN**. Security/reliability independent reviewers NOT present. LOT06 global NOT CONVERGED; HUMAN GATE physical PENDING; clinical NO-GO; no release, purchase, patient, merge, Vercel or cabinet installation.

## Known adversarial edges
- A captured C signature is replayable if the verifier relies only on a caller-provided C packet. `MATCH_LAB_NOT_GLOBAL_FRESHNESS` must not be reinterpreted as an authorization.
- B/C signer and witness DB share one CI runner: their separate logical identities do not constitute separate administrative or rollback domains.
- The checkpoint fixture's updates are volatile, in-process and non-atomic with the B CAS transaction. Its integrity does not survive hostile restore or power loss as a promised property.
- True HSM Ed25519 private key protection and reliable per-decision immutable C checkpoint acknowledgement remain implementation feasibility questions. Real validation exclusively LOT10.
