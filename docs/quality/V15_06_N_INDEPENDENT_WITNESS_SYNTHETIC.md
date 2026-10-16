# LOT06-N — Independent Witness Synthetic LAB — draft protocol

**Date:** 2026-10-16. **Status:** EXPERIMENTAL, synthetic-only, review candidate. **Dependency:** LOT06-M PR #851 / commit 4d1391e7e3faab09966202a3cb6ad93e49d92d6e, Windows/Linux CAS CI GREEN. New PR is DRAFT against LOT06-M feature branch, not master; do not merge without explicit approval. Physical HUMAN GATE remains PENDING and clinical NO-GO.

## Precise topology and evidence ceiling

One GitHub Actions runner hosts a **separate OS process** for a synthetic emitter and another for a synthetic witness. They exchange bounded canonical JSON over 127.0.0.1 with mutually verified Ed25519 request/response signatures and a fresh challenge. The witness uses the **existing isolated LOT06-M durable_cas_lab.py**, synchronous FULL SQLite rollback journal, atomic update of head, op-id ledger and complete signed receipt. Test harness generates the two private test keys and injects each process's test key through its private standard input; they are NEVER persisted in the SQLite database, artifacts, workflow environment or logs.

**Not independent security domains:** a single runner/administrator/harness controls both keys, processes, DB backups and localhost. The witness signing key is retained by the test harness to restart the witness, not protected by a TPM/HSM. The same public pin is explicitly provided to the test client fixture, not approved out-of-band enrollment. This is neither a second machine, separately managed witness, genuine secret custody nor protection against compromise of the runner.

All test input is randomly generated opaque scope/op ids, fixed synthetic digest and SYNTHETIC_ONLY epoch; zero patient media/identifiers, application database tables, services, production keys, clinic IPs or DNS. The server MUST bind 127.0.0.1 only. Do not change an active collector, patient flow or clinical authorization. No Vercel, GitHub Pages, physical installation or merge is authorized.

## Protocol and fail-closed outcomes

- Client signs the canonical strict request (protocol, method, scope, challenge, op_id, event) under the distinct domain DC06N client synthetic-v1. Witness validates strict field shape, fixed enrolled client public key, signature and event binding before accessing the durable CAS.
- Methods: APPLY, LOOKUP, HEAD, and synthetic failure injection DROP_AFTER_COMMIT. The latter performs the durable CAS but sends **no ACK**.
- Witness returns a signed canonical proof bound to the *received* challenge, authority, epoch, scope, method, op_id, current SQLite head and any exact immutable saved Ed25519 receipt. Client verifies witness pin, proof fields and receipt content, and rejects an old challenge (replay), wrong public key, wrong event, malformed evidence and an orphaned or mismatched receipt.
- Distinguish DECIDED_LAB_ONLY, HISTORICAL_ONLY, HEAD_ONLY, UNKNOWN_OP from UNKNOWN_NO_AUTHORITY. **Any missing, malformed, inconsistent, unreachable or untrusted response yields UNKNOWN, never success or clinical ACK.** A persisted signed old receipt can be read for audit but does not authorize current action.
- DROP_AFTER_COMMIT: client gets UNKNOWN; it must LOOKUP the **same** operation ID and/or replay the same exact request, yielding the *same* stored receipt. A changed request under the same op_id refuses without advancing the head.
- Two separate client processes contesting the same predecessor must produce exactly one durable CAS decision. Two identical requests must return identical original receipt bytes. After witness restart, an authenticated HEAD/LOOKUP must expose saved decisions. Offline witness must not accept transitions.

**Explicit negative invariant:** with the test harness restoring an entire old SQLite snapshot **and retaining its old signing key**, the witness can sign an apparently fresh challenge over the old head. Thus independent high-watermark/custody **is still missing**. Fresh signatures alone are not global anti-rollback; no physical failover, real packet loss, real power cut, NTFS/SSD flush ordering, privacy/ops approval or independent human reviewer is provided by this simulation.

## Evidence requirements and gate

- Exact-source GitHub workflow with Windows **and** Linux jobs (not only local machine). Tests explicitly exercise real separate subprocess clients and a separate loopback server process, concurrent same/different op IDs, same-op replay, an ACK drop after durable commit, signer mismatch, scope/nonce tampering, network-outage refusal, server restart, corrupt ledger, signed current-head challenge and rollback counterexample.
- Do not equate an OS subprocess death or soft socket shutdown with an independent physical power cut, WAN partition, or durable high-watermark.
- Internal adversarial A Security and B Reliability may check code, tests, transient errors, false claims and review same SHA. Without two actual independent human reviewers, label these **internal**, with hard BLOCKERs for physical implementation and scores below unsupported >9.5 maturity targets.
- Exit of this **synthetic** lot requires Windows/Linux green exact-head plus valid positive/refusal logs and no major regression. This is a **LAB-only GO** and does not approve witness topology, key custodians, patient data, production or clinical use.

**Next HUMAN GATE:** actual independent admin and storage domain, signer identity/key custody and pin-enrollment chain, protected monotonic checkpoint/high-watermark, single-PC and outage workflow decisions, B0–B9 power-cut/SSD simulations on real hardware and external reviewers. Physical/clinical = NO-GO until separately approved.
