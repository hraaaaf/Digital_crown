# PC-04 — TRIPLE CHECK — ADVERSARIAL

Status: COMPLETE — findings corrected, recertification required
Scope: PR #641 — Patient Companion Consent Vault
Review basis: corrected branch after the initial double check.

## Adversarial questions
- Can a revoked/expired request be silently resurrected?
- Can malformed patient input escape the encrypted domain-result contract?
- Can extra payload fields influence command processing?
- Can a second signature replace the first evidence?
- Can a changed/revoked document still be signed?
- Does CI history create false confidence?

## Finding TC-1 — historical request resurrection
Severity: high for auditability.

Observed:
Reissuing the same document/hash reused an existing revoked/expired request row and reset it to PENDING.

Risk:
Historical state was mutable; revocation/expiry evidence could be overwritten.

Correction:
- removed the uniqueness rule that forced one request per document/hash forever;
- PENDING and SIGNED requests remain idempotent;
- REVOKED and EXPIRED rows remain immutable historical records;
- reissue creates a new request row;
- consent revocation now writes a dedicated audit event;
- targeted history-preservation regression test added.

## Finding TC-2 — invalid signature could escape encrypted ACK
Severity: high for remote-protocol truth.

Observed:
`validate_patient_signature_png(...)` raises `HTTPException` for malformed/blank/oversized signatures. The consent handler did not catch it.

Risk:
The remote command path could return a raw HTTP error instead of a signed/encrypted `REJECTED` domain result, breaking the transport contract and producing inconsistent UX.

Correction:
- signature validation exceptions are converted to `REJECTED / INVALID_SIGNATURE`;
- the remote worker can therefore return the normal encrypted ACK;
- targeted regression test proves no evidence is created.

## Finding TC-3 — permissive command payload
Severity: defense-in-depth.

Observed:
The consent handler accepted extra fields.

Correction:
- exact payload set is now required: `consent_id` + `signature_base64`;
- consent ID is normalized/validated as UUID;
- targeted regression test added.

## Existing invariants rechecked
- changed document version => REJECTED;
- revoked share => REJECTED;
- duplicate signature => REJECTED and original evidence preserved;
- source PDF bytes are not rewritten by PC-04;
- evidence is detached and transactionally persisted with the remote receipt transaction;
- patient UI remains unsigned until cabinet ACK;
- PC-03 historical BEFORE false-red was corrected by making that gate N/A outside PC-03 branches.

## Triple-check conclusion
The prior closeout is superseded for merge purposes.
A fresh exact-head CI/visual/schema/transport certification is mandatory before READY/merge.
