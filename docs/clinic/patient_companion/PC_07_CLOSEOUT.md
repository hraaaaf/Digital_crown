# PC-07 — Emergency Photo — CLOSEOUT

Status: MERGED — POST-MERGE VERIFICATION IN PROGRESS
PR: #648
Product head: 974c364178302cca697dfdfc5a15f85626f19f23
Merge commit: f4576d5127799b66eae891afb82ebd439d8b48d0
Branch: feature/patient-companion-pc07-emergency-photo
Deployment: none

## Goal
Allow a patient to send an emergency photo through Patient Companion to the exact cabinet/patient record using the approved encrypted remote transport, with canonical persistence in Media Core and no false receipt state.

## Success
Observed before merge:
- chunked encrypted-object protocol implemented with `emergency_photo.begin`, `emergency_photo.chunk`, `emergency_photo.finalize`;
- relay 256 KiB limit preserved; raw chunk size fixed at 96 KiB;
- tenant/patient binding derived server-side from active access;
- final persistence only in `ClinicalAsset / Media Core`;
- shared clinical-photo normalization strips metadata and rewrites supported JPEG/PNG/WebP inputs;
- temporary chunks encrypted at rest and bounded by expiry/quota;
- retries are idempotent; conflicting duplicates fail closed;
- local photo bytes use encrypted IndexedDB media storage;
- `received` is set only after authoritative signed cabinet ACK;
- Chromium + WebKit visual evidence passes at 360x800 and 390x844;
- human visual approval received before merge.

## Proof
Exact pre-merge product head: `974c364178302cca697dfdfc5a15f85626f19f23`

- PC-07 Emergency Photo Certification `35588652802` — SUCCESS
- Patient Companion Remote Transport Gate `35588652799` — SUCCESS
- PostgreSQL Alembic Schema Certification `35588652849` — SUCCESS
- PC-07 BEFORE Visual Evidence `35588652855` — SUCCESS
- PC-07 AFTER Visual Evidence `35588652761` — SUCCESS
- CI `35588652925` — SUCCESS
- human visual gate — APPROVED
- PR #648 — MERGED
- merge commit — `f4576d5127799b66eae891afb82ebd439d8b48d0`

## Visual score
9.2 / 10, conservative pre-merge review.

## Residual limitation
Expiry cleanup for unfinished temporary uploads is opportunistic on PC-07 activity. No independent periodic GC is introduced in this lot. Expired uploads remain unusable after expiry checks.

## Not claimed
- no Vercel deployment;
- no LLM/CV image interpretation;
- no public/presigned clinical-media URL;
- no second canonical media store;
- post-merge certification is not claimed until the merge-commit workflows complete.

## Post-merge runs
At closeout creation:
- Cabinet Upgrade PostgreSQL Certification `35589112147` — queued;
- CI `35589112155` — queued;
- additional merge-commit push workflow(s) may still be running.

## Next exact
1. verify merge-commit post-merge workflows;
2. if green, mark PC-07 post-merge verified in canonical docs/Notion;
3. set active lot to PC-08 — Secure Messaging;
4. prepare the PC-08 start handover without deploying Vercel.
