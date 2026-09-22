# PC-08 — Secure Messaging — Certification Candidate

Status: PENDING EXACT-HEAD EVIDENCE
Date: 2026-09-22
Branch: `feature/patient-companion-pc08-secure-messaging`
PR: #677
Deployment: none

## Goal

One access-isolated asynchronous secure text thread between Patient Companion and the owning cabinet, using cabinet-local canonical persistence and the certified Patient Companion remote transport.

## Target → implementation comparison

| Target | Implementation status | Proof status |
| --- | --- | --- |
| Thread isolated by PatientCompanionAccess | canonical model + all queries scoped by access/tenant/patient | code + backend tests added; CI pending |
| Text only, <=4096 UTF-8 bytes | shared body normalizer + byte counter | tests added; CI pending |
| Patient outbound pending until signed cabinet ACK | encrypted pending queue + remote command ACK | code inspected; transport regression pending |
| Staff outbound not falsely delivered/read | labels derived from patient_received_at/patient_read_at | code inspected; visual proof pending |
| Explicit patient received/read | message.received / message.read handlers | backend tests added; CI pending |
| Explicit staff read | authenticated staff read mutation | backend tests added; CI pending |
| Offline patient queue | encrypted vault local_queued/remote_pending | defect found/corrected; test added; CI pending |
| Multi-access staff selector | relationship-labelled access selector | code present; seeded visual proof pending |
| No attachment/push/WhatsApp/LLM | absent from PC-08 runtime | code inspection PASS |
| 20 x 4096 bytes below relay ceiling | real JOSE boundary test | execution pending |
| Mobile 360x800 + 390x844 Chromium/WebKit | AFTER workflow created | artifact pending |
| Staff 390x844 / 768x1024 / 1280x900 | AFTER staff workflow created | artifact pending |
| No horizontal overflow/runtime console errors | asserted by visual scripts | execution pending |

## Known corrections made before certification

1. generic IP rate-limit was not reused as product messaging policy; persistent per-access creation limit implemented;
2. sync semantics corrected to latest snapshot + bounded older pagination;
3. generic remote payload error copy corrected outside PC-08 to avoid “photo” wording;
4. staff UUID validation hardened;
5. staff retry preserves client_message_id after ambiguous failure;
6. patient offline queue restored after adversarial review;
7. staff AFTER workflow corrected to exact PR HEAD.

## Evidence ledger

- PC-08 architecture map: READY
- UI target: READY
- adversarial pre-cert review: READY
- backend domain tests: ADDED / EXECUTION PENDING
- frontend transport test: ADDED / EXECUTION PENDING
- frontend truth-contract test: ADDED / EXECUTION PENDING
- JOSE size boundary: ADDED / EXECUTION PENDING
- PostgreSQL Alembic: PENDING
- Remote Transport Gate: PENDING
- CI: PENDING
- T2: PENDING
- PC-08 BEFORE visual artifact: PENDING
- PC-08 AFTER visual artifact: PENDING
- PC-08 staff BEFORE/AFTER visual artifact: PENDING
- severe visual score: PENDING — must be based on actual artifacts
- independent double check: pre-cert code inspection complete; execution evidence pending
- triple check: PENDING after exact-head green evidence
- human visual approval: PENDING

## Merge gate

DO NOT MERGE until:
1. exact-head required checks are green;
2. actual BEFORE/AFTER artifacts have been inspected;
3. target↔render comparison has no unresolved blocker;
4. severe visual score is recorded from evidence;
5. adversarial triple check is complete;
6. human visual approval is explicit.

No Vercel deployment.
