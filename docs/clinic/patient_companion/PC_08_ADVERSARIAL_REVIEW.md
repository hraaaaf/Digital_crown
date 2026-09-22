# PC-08 — Secure Messaging — Adversarial Review

Status: PRE-CERTIFICATION REVIEW
Date: 2026-09-22
Reviewed branch: `feature/patient-companion-pc08-secure-messaging`

## Scope

Independent adversarial pass over the PC-08 architecture and current implementation before exact-head certification.

## Findings

### Security boundary — PASS by inspection
- canonical messages are scoped by `access_id + employer_id + patient_id`;
- staff routes resolve the patient through existing D2 staff authorization;
- revoked accesses are excluded from staff selection and patient remote commands fail through the existing principal/keyset gates;
- remote `message.*` operations reuse the certified signed/encrypted worker;
- message bodies are not copied into AuditLog details;
- no patient OS-push clinical payload was added;
- no WhatsApp/SMS/LLM/attachment transport was added.

### Truth semantics — PASS by inspection
- patient outbound becomes canonical only from an accepted signed cabinet ACK;
- staff outbound persistence is not labelled received/read;
- patient receipt/read timestamps require explicit `message.received` / `message.read`;
- staff read timestamp requires an authenticated staff mutation;
- relay timeout/pending remains pending;
- local discard removes only a local pending item and does not delete canonical cabinet truth.

### Isolation / idempotency — PASS by inspection
- thread identity is one `PatientCompanionAccess`;
- unique `access_id + client_message_id` adds domain idempotency beyond the remote receipt ledger;
- staff retry preserves the client message ID after an ambiguous failure;
- patient retry persists client/idempotency IDs in the encrypted vault;
- cross-access cursor is fail-closed.

### Offline behavior — issue found and corrected
Initial patient UI disabled send when remote transport was unavailable, contradicting the locked local-queue contract.

Correction:
`b59210b57db4bc5b7493366faf7a71667f33883d`

Now a valid draft can be encrypted and queued locally without claiming cabinet receipt.

### Size proof — implementation added, execution pending
A real JOSE boundary test now constructs 20 maximum-size 4096-byte messages and asserts the final compact JWE remains below the relay 256 KiB ceiling.

Test:
`backend/tests/test_patient_companion_messages_jose_size.py`

Execution result is intentionally not claimed until CI/test evidence exists.

## Residual risks / non-scope

Not certified by PC-08:
- realtime delivery, presence or typing;
- patient OS push;
- attachments;
- message edit/delete/unsend;
- global Connect Hub inbox;
- legal retention duration/export policy;
- remote deletion of already cached device data.

## Pre-certification verdict

No known critical design defect remains from this inspection pass.

This is **not** a final certification. Required proof still pending:
- exact-head backend/frontend tests;
- PostgreSQL Alembic gate;
- remote transport regression;
- real JOSE boundary execution;
- BEFORE/AFTER visual artifacts;
- target↔render comparison;
- human visual approval.

No merge and no Vercel deployment before the human gate.
