## 2026-10-20 bounded signed-replay lab extension — NOT SCM integration
- J10C RSA body/signature/pin wire format is independently checked by `backend/tests/fixtures/lot05j10d_signed_replay_lab.py`; it binds owner/job/generation/manifest, nonce and expiry and reserves a nonce with exclusive marker creation + file fsync, returning **DENY only**.
- Nine synthetic RSA tests cover tamper, false key/owner, expiry, wrong scope, concurrent replay, persistence across function invocations, missing/symlink ledger and no clinical apply. These tests use a *test generated RSA key*, not the genuine installed SCM signer nor an independent vendor pin.
- This module has **NOT** been wired into the real J10D consumer SCM. Windows process restart, ledger rollback/reparse/ACL resistance, power loss and true J10C SCM signing round-trip are **not yet tested**. Do not infer the J10D signer↔consumer gate passed from these Python tests.
- Install-time ACL, signed package provenance and trusted key anchoring remain blockers. Clinical GuidedRestore stays DENY. Not a completed certification.

# LOT05 / 05.7-J10D — installed Windows authority certification gate (OPEN / NO-GO)

Base: J10C `12374a5e3e9f6c16ddf10859f53a8c816077ac36`.
This document is an acceptance contract, NOT evidence of implementation or certification. It does not authorize clinical restore, import, deployment, merge, or widening beyond LOT05/05.7.

## Verified starting point
- J10C's real Windows SCM LocalService signer runs under a Service SID, checks a genuine fake JWT and protected synthetic SQLCipher generation binding, and signs RSA.
- J10C's **consumer** is `backend/tests/fixtures/lot05j10c_bound_sqlcipher_verifier_lab.py`, invoked by a **test process**, not an independently installed SCM worker.
- J10C's ephemeral test admin provisions RSA key, public pin, JWT secret, expected manifest and fake owner/job; no independent vendor/install trust anchor.
- Its nonce ledger is temporary and `shutil.copytree` is an isolated FAKE copy, not transactional clinical recovery.
- J10/J10B functional jobs passed on the stacked J10C HEAD, but their strict file-scope gates failed because the stacked diff contains later-stage files. Do not weaken or relabel those failures.

## REQUIRED J10D proof gates — all must pass on the same immutable HEAD
1. **Installed binaries / provenance.** Reproducible Windows installer or equivalent verifiable installation package; independently pinned signing/publisher identity and binary hashes; distinguish test-runner Administrator/SYSTEM provisioning from product authority. A CI-generated key or pin alone is a FAIL.
2. **Two actual SCM services.** Install, start, stop and clean up a distinct signer and consumer service; capture SCM service config, identity, SID type, executable path/hash and process token proof. Neither a child Python verifier nor a script in the test runner counts as an installed consumer.
3. **Authenticated IPC.** Specify and test a concrete IPC channel with OS-enforced caller identity, message framing, nonce, purpose, owner/job/generation/manifest binding, expiry, authenticated peer and explicit deny on spoofed peer, unauthenticated request, replay, tamper, downgrade and cross-tenant request. A signed file in a writable handoff directory alone does not count.
4. **OS isolation / adversarial.** Exercise a same-account SID-less service and a separate unprivileged service against executable, pin, secret, request, output and IPC; fail closed. Include junction/reparse/path swap attempts and handle-anchored file verification, with explicit disclosure of what Admin/SYSTEM can still alter.
5. **Independent trust root.** Demonstrate provenance of trusted public key and signer binary from outside the test administrator's control. Explicitly define the threat model for local Administrator/SYSTEM; if it cannot be resisted, declare that boundary, never claim admin-resistant attestation.
6. **Audit / consent.** Verify authenticated operator authorization and durable, non-secret audit linkage to owner/job/generation; no human consent means clinical apply remains DENY.
7. **Failure tests.** Real process termination, SCM restart, interrupted IPC, stale generation and duplicate ticket; no unsigned acceptance, no replay, no output modification, no clinical side effect. Power loss and rollback resistance remain separate unresolved clinical gates.
8. **CI and review.** Strict J10D-only changed-file gate relative to exact J10C base; Windows evidence artifacts without keys/JWT/PHI; test counts and failures; two independent adversarial reviews on the same HEAD. Do not infer historical J10/J10B gate green on a stacked HEAD.

## Forbidden shortcuts
- Do not modify `GuidedRestoreService.request_apply` or `GuidedRestoreWorker.run` to permit apply.
- Do not reuse the test runner's ephemeral RSA pin as proof of product provenance.
- Do not use a CI green marker or SCM signer alone as a product certificate.
- Do not weaken historical strict scope gates, merge stacked PRs, deploy, or touch LOT06/LOT10/mobile.
- Do not use real patient data.

## Release decision
**J10D OPEN; LOT05 product NO-GO.** This contract alone satisfies zero implementation gates. Actual installed worker + IPC + independent trust evidence and exact-HEAD CI are required before any positive certification claim. Clinical atomic DB/WAL/SHM + media/vault restore, crash/powerfail, RPO/RTO and rollback safety are a subsequent LOT05 gate, not covered by J10D.
