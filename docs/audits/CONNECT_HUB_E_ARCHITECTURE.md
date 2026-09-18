# Digital Crown — LOT E — Connect Hub Architecture Contract

Status: **CLOSED — merged and certified**
Implementation branch: `feat/lot-e-connect-hub` (merged via PR #557)
Base at start: `49db132882ba5b352ae761bda34e1a9fa3d82e27`
Canonical roadmap: `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`

## Goal

Create one unified patient/cabinet communication surface **above** Digital Crown's existing notification infrastructure, without creating a second notification engine, transport, source of truth, or convenience dual-write.

## Success

LOT E may implement only if the following remain true:

1. Web Push registration/delivery remains canonical through `mobile_push_subscriptions`, `backend/routers/mobile_push.py`, `backend/services/mobile_push_service.py` and the central mobile notification policy.
2. Legacy FCM `/register-device` remains unmounted; historical `DeviceToken/device_tokens` is not reactivated or written by Connect Hub.
3. Appointment reminder SMS/WhatsApp behavior remains delegated to the existing notification service; Connect Hub does not implement a replacement SMS/WhatsApp sender.
4. Existing alert/notification/preferences sources are aggregated at read time where possible; no generic Connect Hub notification table is introduced merely for UI convenience.
5. Tenant/user/patient authorization is enforced at the canonical source/action boundary, not only hidden in the UI.
6. Delivery state is represented only at the level actually proved by the underlying transport. A mock/simulated return value must never be presented as externally delivered.
7. Meaningful mutations are auditable through existing audit mechanisms or an explicitly justified extension.
8. No patient-facing public/unscoped document or media fallback is introduced.
9. Existing DB/data/functionality is preserved; no destructive migration is part of this initial LOT E contract.

## Source / action / status matrix

| Capability | Canonical source/action | Connect Hub role | Allowed status claim |
|---|---|---|---|
| Mobile OS Push registration | `mobile_push_subscriptions` + `/push/subscription` | Present/configure existing capability | Registered only when canonical subscription exists |
| Mobile OS Push delivery | `mobile_push_service.send_push_for_alert_types` | Delegate/orchestrate | Generic push attempt/sent count only as returned by canonical service |
| Mobile notification authorization | `mobile_notification_policy` | Reuse | Eligible/ineligible according to canonical policy |
| Appointment reminder SMS | `notification_service` | Delegate existing action | Never claim external delivery beyond evidence exposed by the service |
| Appointment reminder WhatsApp | `notification_service` | Delegate existing action | Never claim external delivery when transport is mock/simulated |
| Existing alerts/notifications | Existing canonical alert/notification sources | Aggregate/read-model | Source state only; no duplicate persistence |
| Preferences | Existing notification/user preference mechanisms | Read/update canonical preference boundary only | Persisted preference only after canonical mutation succeeds |
| Audit | Existing `AuditLog` / canonical action audit | Surface/reference | Audited only when audit record/action is actually persisted |

## Explicit exclusions

LOT E initial implementation MUST NOT:

- create a second Push engine, FCM sender, APNs sender, VAPID store or push subscription table;
- revive `POST /register-device` or write historical `DeviceToken` rows;
- create a generic `connect_hub_notifications` table for mirrored data;
- duplicate Patient, Appointment, Document, Media, Alert or User models;
- infer a delivery receipt that the provider/runtime did not prove;
- silently treat mock SMS/WhatsApp behavior as production delivery;
- add Patient Companion transport/auth behavior;
- introduce public/unscoped media/document URLs;
- perform a destructive DB migration;
- deploy to Vercel without explicit owner authorization.

## Initial product boundary

The first Connect Hub slice is a **cabinet-side unified communication read surface** with safe delegated actions. It should answer, without copying data:

- what communication/notification items require attention;
- which patient/cabinet context each item belongs to when the source authorizes that context;
- which canonical channel/action is available;
- what state is actually known versus unknown/unverified.

The first slice is not a new omnichannel delivery platform.

## UI gate

Before visual implementation:

1. capture BEFORE at the selected existing cabinet surface and canonical responsive viewports;
2. write the exact UI Goal;
3. create/record the reference or mockup;
4. implement;
5. capture AFTER at the same viewports;
6. compare Target ↔ Render and test responsive/accessibility behavior;
7. assign visual score only from observed evidence.

No visual fidelity score above 7.5/10 without real Target ↔ Render comparison.

## Implementation gate

Architecture contract is ready for implementation only after current sources are rechecked on the branch and no active duplicate transport/source is demonstrated.

Current known residual: historical `DeviceToken/device_tokens` schema remains for compatibility. It is dormant by contract and must not be used by LOT E.

## Definition of Done

Follow the canonical roadmap DoD: anti-dup audit, bounded scope, implementation, automated/security/isolation tests, UI certification if visual, docs/migrations reconciliation, exact-head CI, PR discussion/mergeability audit, merge, post-merge verification, canonical closeout with exact evidence.


## Closeout evidence

LOT E is closed. The implementation was merged via PR #557 as merge commit `7c175bdd37b2f53afb7b05fd8cf21aaf4bda2164`.

Verified implementation head before merge:
- `ad171dd559bd6af517e57ea945de4c03317c1b72`
- CI #4813 / run `35241949730`: SUCCESS.
- Connect Hub E Backend Certification #7 / run `35241949680`: SUCCESS.
- Connect Hub E AFTER #10 / run `35241949717`: SUCCESS.
- AFTER artifact `10505184198`, digest `sha256:d9dcacb39eeca88a44ae3740d3097c8f887e865e5516089398178efcefffed39`.

The immediate post-merge global CI #4814 / run `35245309329` failed outside the Connect Hub scope after 3746 backend tests passed: the single failure was `backend/tests/test_vision_apex_provenance.py::test_pytorch_landmarks_do_not_gain_synthetic_incisor_apices`, with the legacy Céphalo model import unavailable. The Frontend job and production guard were SUCCESS.

Subsequent repository reconciliation repaired Linux dependency / Connect Hub contract drift via PR #583. Exact repair evidence recorded by the consolidated V1 roadmap:
- Connect Hub E run `35282100413`: SUCCESS.
- CI run `35282100416`: SUCCESS.
- PR #583 merge: `bc7e1e1f1762431a048661ad9495a3430774f6e0`.

Current master `a18a84cb50f34f2a95263e75e581b379dab334c8` retains LOT E and has CI #4956 / run `35364084023`: SUCCESS.

Canonical closeout: `docs/audits/CONNECT_HUB_E_CLOSEOUT.md`.
