# Digital Crown — LOT E — Connect Hub Closeout

Date: 2026-09-18
Status: **CLOSED**
Architecture: `docs/audits/CONNECT_HUB_E_ARCHITECTURE.md`
UI gate: `docs/audits/CONNECT_HUB_E_UI_GATE.md`
Canonical V1 roadmap: `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`

## Goal

Deliver one cabinet-side unified attention/communication surface above the existing Digital Crown notification infrastructure, without creating a second notification engine, transport, persistence source of truth or dual-write.

## Delivered boundary

- read-time aggregation of existing ProactiveAlert and treasury sources;
- tenant/RBAC checks at source boundaries;
- canonical route `/api/intelligence/connect-hub`;
- one header attention entry point;
- truthful `source_state_only` delivery semantics;
- legacy FCM registration remains disabled;
- no generic Connect Hub notification table;
- no destructive migration;
- no Vercel deployment was required for this lot.

## Product merge

- PR #557: merged.
- certified implementation HEAD: `ad171dd559bd6af517e57ea945de4c03317c1b72`.
- merge commit: `7c175bdd37b2f53afb7b05fd8cf21aaf4bda2164`.

## Exact-head evidence before merge

- CI #4813 / run `35241949730`: **SUCCESS**.
- Connect Hub E Backend Certification #7 / run `35241949680`: **SUCCESS**.
- Connect Hub E AFTER #10 / run `35241949717`: **SUCCESS**.
- no unresolved PR review threads at merge gate.

### BEFORE visual evidence

- baseline product SHA: `49db132882ba5b352ae761bda34e1a9fa3d82e27`.
- run `35202983003`: **SUCCESS**.
- artifact `10488787031`.
- digest: `sha256:dac724723b62dd8cc8f6bedecf749dca4e0d27085f6aeb882197d474096edffa`.
- viewports: 390×844, 768×1024, 1280×900.

### AFTER visual evidence

- run `35241949717`: **SUCCESS** on `ad171dd559bd6af517e57ea945de4c03317c1b72`.
- artifact `10505184198`.
- digest: `sha256:d9dcacb39eeca88a44ae3740d3097c8f887e865e5516089398178efcefffed39`.
- same canonical viewports inspected.
- visual score retained: **9.2/10**.
- human visual validation obtained before merge.

## Post-merge reconciliation

Immediate global CI #4814 / run `35245309329` on merge commit `7c175bdd…` was not green:
- frontend: SUCCESS;
- production guard: SUCCESS;
- backend: 3746 passed / 10 skipped before one failure;
- sole failure: `backend/tests/test_vision_apex_provenance.py::test_pytorch_landmarks_do_not_gain_synthetic_incisor_apices`;
- log cause: unavailable legacy Céphalo model module `models`;
- this failure was outside the Connect Hub implementation boundary.

The repository later reconciled Linux dependency / contract drift through PR #583:
- exact repair HEAD `7b3d89248405296b8503d5eb16d4e54059057dee`;
- Connect Hub E run `35282100413`: **SUCCESS**;
- CI run `35282100416`: **SUCCESS**;
- PR #583 merge: `bc7e1e1f1762431a048661ad9495a3430774f6e0`.

Current master at closeout preparation:
- `a18a84cb50f34f2a95263e75e581b379dab334c8`;
- CI #4956 / run `35364084023`: **SUCCESS**;
- consolidated V1 roadmap records Connect Hub Lot E as merged and identifies historical Lot F — Ortho Journey as the next competitive lot.

## Anti-duplication / safety result

The architectural invariants remain the closeout contract:
- existing Web Push stack remains canonical;
- historical DeviceToken/register-device is not reactivated;
- SMS/WhatsApp delivery is not reimplemented or overclaimed;
- existing source data is aggregated rather than copied;
- authorization is enforced server-side;
- mock/simulated states are not presented as externally delivered;
- no public/unscoped patient media/document fallback is introduced.

## Gate final

LOT E — Connect Hub is **CLOSED**.

Observable success:
1. product implementation is merged;
2. targeted backend and exact-head CI were green before merge;
3. responsive UI passed AFTER automation and human review at 9.2/10;
4. later Connect Hub + global CI repair evidence is green;
5. current master CI is green;
6. architecture and UI gate documents are reconciled by this closeout.

Next historical competitive lot: **Lot F — Ortho Journey**, already represented in the consolidated V1 roadmap.