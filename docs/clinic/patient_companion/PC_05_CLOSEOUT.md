# PC-05 — Patient notifications — CLOSEOUT

Status: FINAL CLOSEOUT CANDIDATE — RECERTIFY THIS DOC COMMIT BEFORE MERGE
Branch: feature/patient-companion-pc05-notifications
PR: #643
Certified product HEAD: 113a51fbd2423b966a74e0c67239169730b55f2d
Base: master@c9cd8e9b1220b7b98691d9889cbb856d0650e40b
Deployment: none

## Goal
Expose a patient-safe notification center in Patient Companion by projecting existing canonical domain state, without creating a second notification engine, second transport, generic parallel persistence, or dual-write path.

## Verified architecture
- notification content is projected from canonical agenda, shares, questionnaires and consent state;
- PC-05 persistence is limited to per-access notification preferences and receipts;
- no notification title/body/domain payload is duplicated as business truth;
- patient mutations reuse the existing encrypted Patient Companion remote command transport;
- read/snooze/preferences become authoritative only after durable cabinet ACK;
- relay pending never claims accepted/read/snoozed/updated state;
- deterministic notification identifiers are derived from access + canonical source key;
- tenant/patient/access isolation is enforced on receipts and preferences;
- revoked Patient Companion access fails closed;
- refused/expired appointments are excluded;
- signed or mismatched consent shares do not resurface incorrectly as actionable notifications;
- M6-D2 staff push identity is not reused as patient identity;
- no real patient OS-push delivery claim is made in PC-05;
- existing no-PHI/generic OS notification doctrine remains unchanged.

## Double / triple check
The required double and adversarial triple checks were completed before closeout.

Verified findings:
- canonical source uniqueness preserved;
- only receipt/preferences-specific persistence added;
- no second crypto/relay/notification engine added;
- access revoked fails closed;
- mismatched consent shares fail closed;
- signed consent does not duplicate as generic document alert;
- refused/expired appointments do not notify;
- read/snooze/preferences do not optimistically mutate UI state before ACCEPTED ACK;
- idempotency replay yields one durable mutation and one audit result;
- receipt lookup is scoped by access_id + employer_id + patient_id.

## Exact-head certification — 113a51fbd2423b966a74e0c67239169730b55f2d
- PC-05 Patient Notifications Certification: 35541732798 — SUCCESS
- CI: 35541732812 — SUCCESS
- PostgreSQL Alembic Schema Certification: 35541732797 — SUCCESS
- Patient Companion Remote Transport Gate: 35541732853 — SUCCESS
- T2 Runtime Browser Certification: 35541732803 — SUCCESS
- PC-00 Patient Companion Visual Certification: 35541732922 — SUCCESS
- PC-02 BEFORE Visual Evidence: 35541732825 — SUCCESS
- PC-02 AFTER Visual Evidence: 35541732834 — SUCCESS
- PC-03 AFTER Visual Evidence: 35541732846 — SUCCESS
- PC-04 AFTER Visual Evidence: 35541732809 — SUCCESS
- Agenda A5 Visual Evidence: 35541732866 — SUCCESS
- PC-05 BEFORE Visual Evidence: 35541732839 — SUCCESS
- PC-05 AFTER Visual Evidence: 35541732826 — SUCCESS
- PR Merge Summary: 35541732814 — SUCCESS
- M6-I Biometric Passkey Certification: skipped as expected
- PC-04 BEFORE Visual Evidence: failure is unrelated to PC-05 and corresponds to the known historical true-BEFORE harness limitation on later branches.
- Patient P7 Final Certification: 35541732880 was still in progress at the last pre-closeout check and MUST be rechecked on the documentation HEAD before merge.

## Certification defect corrected during PC-05
A focused PC-05 test exposed an architectural coupling in `process_remote_envelope`: loading the full remote registry imported PC-02, which traversed the router package into the vision/OpenCV stack.

Correction:
- remote handlers are now resolved lazily by operation namespace;
- `notification.*` loads only the PC-05 registry;
- `agenda.*` and `consent.*` preserve their existing handlers;
- the focused PC-05 certification then passed backend contracts, frontend truth-boundary tests, and production build on the exact product HEAD.

This was a transport-registry decoupling fix, not a weakening of test dependencies.

## Exact-head visual evidence
BEFORE:
- run: 35541732839 — SUCCESS

AFTER:
- run: 35541732826 — SUCCESS
- artifact id: 10615575989
- artifact name: pc05-notifications-after
- digest: sha256:dd56adb7fe253b9254c26f41cad14d4e152b61cece481610a522bb489d2e55cb

Matrix inspected manually:
- Chromium 360x800
- Chromium 390x844
- WebKit 360x800
- WebKit 390x844
- horizontalOverflow=false on all four AFTER captures

Manual review:
- Notifications is coherently placed between Agenda and Consent Vault;
- information hierarchy remains readable at 360 px;
- settings and actions remain usable and visually distinct;
- no clipping or horizontal overflow observed;
- Chromium/WebKit rendering is consistent.

Severe visual score: 9.1/10.

Residual non-blocking reserve:
- vertical density increases when settings and several notifications are open simultaneously;
- this is explicitly deferred to PC-FINAL — Polish & Visual Consistency.

## Human visual approval
Achraf explicitly approved the exact-head PC-05 visual captures on 2026-09-20 after inspection of the four AFTER screenshots listed above.

## Success criterion
Met for product HEAD 113a51fbd2423b966a74e0c67239169730b55f2d, subject to recertification of this closeout documentation commit itself before merge.

## Merge rule
This closeout commit changes the PR HEAD. It MUST be recertified on its exact HEAD before PR #643 is merged.

No Vercel deployment is authorized or performed as part of PC-05 closeout.
