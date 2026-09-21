# PC-07 — Emergency Photo — CLOSEOUT

Status: MERGED — FINAL POST-MERGE VERIFICATION PENDING
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

## Post-merge repair chain
Observed after PR #648 merge, with each issue repaired and revalidated before continuing:
- #659 → `373092345dadad8aee0949eb9c8650f489eee5b2`
- #661 → `d18a44421f661d055ea8ffe2ddccfa998a966552`
- #662 → `ca7a16de06d80cdc37f01769e9b96a6866b6c2fc`
- #664 → `e9f8df5144be6c95b8a1ad59a4d9f502c2709868`
- #666 → `b9bd8a2c3bb390582148009d0634fe872425d82d`
- #669 → `4adb6b942bb4d184ddfd72a04cf9650294395c6b`
- #670 → `9adfe9ff1d1633f12821027b31338cb667affec6`
- #672 → `671b130b3456ec65a8c108475a54577e6fce47da`
- #674 → `2ddd8ab10beabbf164216eda2d42e577f20fe6d4`
- #675 → `3c1822fec10986158e809d93fb76716bf4890e0a`

The final failing full-backend run before #675 was CI `35614726642`: 2 failed, 4050 passed, 11 skipped. Both failures were stale test expectations, not runtime defects:
- agenda slot assertion needed an ORM refresh after the atomic SQL claim;
- demo email tests did not configure `ADMIN_NOTIFICATION_EMAIL`.

PR #675 exact-head `260f67c72b6eb7a5bc4ae7f12b31b013a41ebfc8` passed CI `35616706913`, Remote Transport `35616706782`, Agenda A5 `35616706778`, T2 `35616706831`, PR Merge Summary `35616706906`, and P7 `35616706810`, then merged as `3c1822fec10986158e809d93fb76716bf4890e0a`.

## Final post-merge state
Current master: `3c1822fec10986158e809d93fb76716bf4890e0a`.

Final post-merge workflows for this merge commit were not yet registered at the time of this documentation update. Therefore PC-07 is not yet declared `POST-MERGE VERIFIED`.

## Next exact
1. verify merge-commit post-merge workflows;
2. if green, mark PC-07 post-merge verified in canonical docs/Notion;
3. set active lot to PC-08 — Secure Messaging;
4. prepare the PC-08 start handover without deploying Vercel.
