# LOT06-N — Durable CAS synthetic SQLite witness LAB v1

**Status:** experimental-only, isolated disposable filesystem fixture; **NOT** a physical independent witness, not clinical approval, no use of production DB. **PR:** #851 DRAFT. **Controlling architecture:** `V15_06_M_DURABLE_AUTHORITY_ADR.md` §22 and `V15_06_M_HUMAN_GATE_DECISION_PACKET_V1.md`.

## Goal and observed admission criteria

Implement a bounded single-file SQLite CAS **simulation** on temporary test directories, with real independent OS child processes competing for the same parent, atomic durable (SQLite transaction) change of monotonic `(sequence, mac)` head and immutable `(op_id, request_bytes, signed_receipt_bytes)` ledger, and controlled **process death** before/after commit. Private Ed25519 key generated in test fixture and delivered through transient stdin to child only. A transaction signs *before* commit, stores the exact receipt bytes in same transaction, and exposes those bytes only after the commit returns. No trusted external key custody or authenticated remote-head endpoint exists.

The lab only opens `witness-synthetic.sqlite` within an automatically created `dc06m-cas-synthetic-*` temporary directory and refuses a symlink DB path. It never accesses app database, imaging media, patient identifiers, CLI collection, Azure/Vercel or Windows services. Database creation is explicit (no `mode=rwc` on recovery). SQLite DELETE journal mode and FULL synchronous are checked. These settings do **not** prove actual physical drive flush durability on every Windows configuration or SSD.

## Invariants / refusal expectations

1. `BEGIN IMMEDIATE` serializes competing writers to the **same** SQLite database file; a different `op_id` with same previous head must refuse with `STALE_OR_FORK_REFUSE`. Identical canonical request & `op_id` returns the *exact persisted receipt*; same `op_id` + different canonical bytes refuses even after head advances.
2. A versioned synthetic canonical request binds random opaque `scope`, `op_id`, epoch, previous/next seq+mac, phase, manifest digest and synthetic key ID. A versioned signed receipt includes SHA-256 of entire request, relevant event bindings, scope and epoch, explicitly labeled `ACCEPTED_LAB_NOT_CLINICAL`. All patient fields are rejected.
3. Head, ledger and signed receipt bytes are written in **one SQLite transaction**; a signer failure leaves no decision. A process terminated before commit leaves the old head and no ledger entry. A process terminated after commit but before sending ACK leaves a recorded decision queryable with the same `op_id` (idempotent retry).
4. `apply` audits the complete bounded ledger before extending it. `lookup` and `audit` read consistent SQLite snapshots and reject tampered request/receipt/head/signing pin. The lab limit is 256 records; this is an admission/fail-closed budget, not a throughput guarantee.
5. An old database file restored with its old internal head **will still pass this local audit** under the same pinned signer. This is an intentionally exercised *negative* demonstration of missing **external trusted high-watermark and independent witness domain**.

## Failure matrix and executable test cases

| Scenario | Expected proof |
| --- | --- |
| Two OS child processes, different op ids, same parent | Exactly one `DECIDED_LAB_ONLY`, the other `STALE_OR_FORK_REFUSE`, ledger count 1 |
| Two OS child processes, same op and bytes | Both return identical persisted receipt bytes, ledger count 1 |
| Identical replay after later successor | Returns same historic receipt, never current-head authorization |
| Same op_id rebound to another request | `OP_ID_REBIND_REFUSE`, ledger unchanged |
| Simulated signer fault before SQL commit | No durable decision or head advance |
| `os._exit(86)` before commit | SQLite rollback after restart, no ACK and no decision |
| `os._exit(87)` after commit | No ACK, durable decision found after restart, same-op retry stable |
| Tampered signed receipt or request, torn head, bad pin | Refusal, no new accepted write, audit failure |
| Nonexistent DB or improper path | No implicit re-enrollment, no use of non-lab path |
| Restore old DB with old internal state | Audit passes **OLD** state: global anti-rollback NOT proven |

## Threat model, gates and safety boundaries

- SQLite transaction atomicity and `synchronous=FULL` are verified via **process death** and file reopen in CI, not real power interruption, NTFS storage barriers, SSD/RAID cache flushes or fault injection at device level. Two local child processes share the host, database file and administrative domain, not two independent LAN witness machines.
- Signing private key lives in the **parent test fixture and child stdin pipes** and is *not* physically isolated. Any compromise of test operator can roll back DB and key material; public pin comes from the same fixture, not independently enrolled.
- Scope is synthetic; no media or patient data. `COMMITTED_LOCAL`, clinical B2 ACK, key escrow, capture coordinator, network isolation and real LAN witness are NOT implemented. The result does not approve a single-computer clinical fallback.
- B0–B9 **physical** recovery gates still need trusted host isolation, independent high-watermark, key custody / epoch rotation and actual power-cut/cross-host restore tests. This LAB covers only selected pre/post-commit process-death and concurrency fragments of that matrix.
- Review status follows exact SHA + CI + two **internal** adversarial perspectives (not genuinely independent reviewers). Target >9.5/10 for full LOT06-M remains NOT MET. PR stays DRAFT, no merge, physical provisioning, patient operations or deployment.

## How to reproduce

`python -m pip install 'cryptography>=42,<48'`

`python -m unittest discover -s tools/imaging_gateway/tests -p 'test_durable_cas_lab.py' -v`

Workflow: `.github/workflows/v15-06m-durable-cas-lab.yml` (Windows and Linux GitHub-hosted runners, temporary lab only). GitHub run URLs, observed counts and HEAD must be entered in PR review and Notion POST **after** they are verified; no preemptive CI claim.
