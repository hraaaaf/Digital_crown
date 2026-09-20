# HANDOVER — Digital Crown / Patient Companion PC-05 — Patient notifications

Date: 2026-09-20
Repository: hraaaaf/Digital_crown
Target next lot: PC-05 — Patient notifications

## Previous lot — PC-04 closed
PR: #641 — feat(patient-companion): PC-04 patient-facing Consent Vault
Final PR HEAD: 68eda3b651e275bbd4082479ef20b27dfa181fb6
Merge commit: 5103baed10aa45966519948fa51c048ae3b300de
Merged at: 2026-09-20T21:44:16Z
Deployment: none

PC-04 closeout:
- docs/clinic/patient_companion/PC_04_CLOSEOUT.md
- docs/clinic/patient_companion/PC_04_DOUBLE_CHECK.md
- docs/clinic/patient_companion/PC_04_TRIPLE_CHECK.md

## PC-04 final proof before merge
Final closeout HEAD: 68eda3b651e275bbd4082479ef20b27dfa181fb6

Exact-head green:
- CI 35538743695
- PostgreSQL Alembic 35538743688
- Patient P7 35538743686
- T2 Runtime Browser 35538743725
- Patient Companion Remote Transport 35538743705
- PC-00 Visual 35538743755
- PC-02 BEFORE 35538743690
- PC-02 AFTER 35538743731
- PC-03 AFTER 35538743745
- Agenda A5 35538743726
- PC-04 BEFORE 35538743691
- PC-04 AFTER 35538743694

Expected skips:
- PC-03 BEFORE 35538743716
- M6-I 35538743710
- PR Merge Summary 35538743779

Final PC-04 visual evidence:
- BEFORE artifact 10613344549
- BEFORE digest sha256:9ceffd9f1a1c2c221b1c361a41381356f50638baa4dcaf90919c7698b26b2a90
- AFTER artifact 10614115300
- AFTER digest sha256:14800bcb4e14af26a59470a37a847dde2dc5e5efcdb2c1f888d8908dd0cd513e
- Chromium + WebKit
- 360x800 + 390x844
- horizontalOverflow=false on all captured viewports
- severe visual score: 9.0/10
- remaining vertical-density polish is assigned to PC-FINAL.

## PC-04 architectural decisions to preserve
- explicit PatientCompanionShareGrant remains the admission gate for patient-shared documents;
- consent is bound to exact document group/version/SHA-256/size;
- physical file integrity is rechecked before read/sign;
- patient must read the exact document before signature UI is exposed;
- patient signature evidence is detached from source PDF;
- source PDF bytes are not silently rewritten by PC-04;
- SIGNED is only shown after durable encrypted cabinet ACK;
- remote pending remains non-signed;
- revoked/expired requests are preserved historically and reissue creates a new row;
- malformed signatures stay inside encrypted REJECTED domain ACK;
- no qualified electronic signature/eIDAS/PKI/legal-retention claim.

## PC-05 canonical goal
PC-05 — Patient notifications.

Start by reading the canonical Notion page:
Digital Crown V1-07 — Pre-freeze Triple-Check Handover — 2026-09-19
Notion page id: 3e077c66-3362-8187-8f6c-ce982280f64d

Do not invent PC-05 detail beyond what the canonical roadmap supports. First inspect existing primitives and lock Goal / Success / Proof before implementation.

## PC-05 anti-duplication — already verified
Do NOT create a second notification engine, transport, generic notification table, or dual-write path without proving existing primitives cannot satisfy the requirement.

Existing primitives to inspect/reuse:

### ProactiveAlert / mobile notification center
PR #256 — M6-D1 — Centre de notifications mobile
Key files:
- backend/routers/mobile.py
- backend/tests/test_mobile_m6d_notifications.py
- frontend/src/features/mobile/Dashboard/components/MobileNotificationCenter.tsx
- frontend/src/test/mobileM6D1Notifications.test.tsx

Known behavior:
- tenant-scoped notifications;
- read + snooze 24h;
- RBAC filtering;
- existing ProactiveAlert truth reused instead of a second engine.

### Web Push device-bound
PR #258 — M6-D2 — Push PWA/OS device-bound
Key files:
- backend/models_mobile_push.py
- backend/routers/mobile_push.py
- backend/services/daily_scheduler.py
- backend/services/mobile_notification_policy.py
- backend/services/mobile_push_service.py
- backend/services/push_service.py
- frontend/public/push-sw.js
- frontend/src/services/zka/mobilePush.ts
- backend/tests/test_mobile_m6d2_push.py

Important inherited constraints:
- device-bound subscription;
- revoked devices fail closed;
- generic lock-screen payload only;
- no patient name, amount, motif, clinical content or PHI in OS payload;
- HTTPS / secure-context expectations;
- no claim of real-device delivery unless physically proven.

### Mobile Notifications cockpit
PR #359 — MOB-5C
Key files:
- frontend/src/features/mobile/Dashboard/views/NotificationsView.tsx
- frontend/src/features/mobile/Dashboard/views/NotificationsView.test.tsx
- frontend/src/features/mobile/Dashboard/MobileDashboard.tsx
- frontend/src/features/mobile/bridge.ts
- docs/ux/DIGITAL_CROWN_MOBILE_NOTIFICATIONS_MOB5C_AUDIT.md
- docs/ux/DIGITAL_CROWN_MOBILE_NOTIFICATIONS_MOB5C_PROOF.md

### Connect Hub
PR #557 — Connect Hub Lot E
Key files:
- backend/routers/connect_hub.py
- backend/tests/test_connect_hub_contract.py
- backend/tests/test_connect_hub_runtime.py
- docs/audits/CONNECT_HUB_E_ARCHITECTURE.md
- docs/audits/CONNECT_HUB_E_UI_GATE.md

Architectural truth from this lot:
- unified communication surface must sit above existing notification infrastructure;
- no second notification engine;
- no second transport;
- no generic parallel persistence table;
- no dual-write;
- do not label simulated SMS/WhatsApp as delivered.

## Patient Companion primitives available
- Patient Companion identity/access/context security is already established.
- Generic encrypted remote-command transport exists:
  frontend/src/features/patient-companion/PatientCompanionRemoteCommandTransport.ts
- PC-02 Agenda transport is a thin wrapper on this generic transport.
- PC-04 Consent transport is another thin wrapper.
- Patient Companion remote worker already supports domain-handler registration and encrypted ACK semantics.

Use these patterns if PC-05 requires patient-side acknowledgement/mutation. Do not create another crypto/relay protocol.

## Mandatory PC-05 working doctrine
Before implementation:
1. read this handover completely;
2. verify current master/HEAD and post-merge state of PC-04;
3. read canonical Notion PC-05 scope;
4. inspect M6-D1, M6-D2, MOB-5C and Connect Hub code/docs;
5. write PC-05 Goal / Success / Proof;
6. perform anti-duplication audit;
7. create BEFORE evidence if UI changes;
8. define UI target/mockup before visual implementation.

For every meaningful PC-05 change:
- double check;
- triple adversarial check;
- code + tests + observed behavior;
- exact-head CI;
- visual BEFORE/AFTER same viewports if UI changes;
- severe visual score;
- no Vercel deploy without explicit authorization.

## Known cross-cutting rules
- ZERO LLM runtime in Digital Crown V1.
- On-prem/local product model.
- Patient data/security changes must fail closed.
- Never display delivery/signed/confirmed state before durable authoritative ACK.
- Preserve Patient Companion tenant/patient isolation.
- No Vercel deployment unless explicitly authorized.
- PC-FINAL — Polish & Visual Consistency remains mandatory after PC-10.
- PC-FINAL owns remaining cross-module vertical-density/visual-consistency debt.

## Post-merge gate status
At the moment this handover was written, PR #641 is merged at 5103baed10aa45966519948fa51c048ae3b300de.
Fetch workflow runs on that exact merge commit before starting PC-05 implementation and record their status. If post-merge runs are pending, continue independent PC-05 audit/preparation but do not falsely declare post-merge certification complete.

## Next exact
1. Fetch workflow runs for merge commit 5103baed10aa45966519948fa51c048ae3b300de.
2. Verify master points to/contains that merge commit and PR #641 is merged.
3. Read canonical Notion PC-05 scope in full.
4. Inspect/reconcile ProactiveAlert + Web Push + Connect Hub + Patient Companion context.
5. Write PC-05 START / Goal / Success / Proof.
6. Only then implement.

## Required continuation behavior
Do not stop for CI merely being queued. Continue all independent audit/architecture/UX work.
Do not ask for confirmation unless a real human gate appears.
