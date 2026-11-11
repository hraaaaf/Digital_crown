# DIGITAL CROWN V1.5 — LOT08.2-B — Local Command & Replay FUE-I

Date: 2026-11-09. Repository: hraaaaf/Digital_crown. PR #1239 OPEN/DRAFT, base master 324afd13487acf7ff29223f077451927b54b8178, before HEAD a642bb38d26c5b6420456fc02867e2da8ea5d6b7. No merge, deployment or real clinical data. User GO: replace compulsory independent-review default with proportionate FUE, retaining risk-specific security oracles.

## Actual runtime and isolation

Previously existing: pure Queue Core domain transitions, standalone SQLAlchemy persistence models, B-2 local operator SQLite identity. No queue HTTP routes, SSE server, native installer or Wall/Kiosk device identities exist. The new queue_core/service/authorized_queue.py implements a local in-process command/replay adapter, NOT HTTP/SSE. It does not create schemas, migrate data, start a server, access clinical databases or enroll production operators.

Auth SQLite and Queue SQLite MUST be two distinct, existing, local files. In each call the adapter first acquires an identity SQLite BEGIN IMMEDIATE transaction and re-resolves the live operator, then acquires Queue SQLite BEGIN IMMEDIATE. Both locks remain held until queue state and audit events commit. B-2 revoke/disable/password reset also need the identity write lock: a command which passed authorization cannot race with a committed revoke before its own queue commit. SQLite FK, version checks and event uniqueness apply; no cross-database atomicity or physical Windows ACL proof is claimed.

Queue, visit tenant and resource-to-visit association are read from trusted persisted rows, not from client claims. RECEPTION can check-in; STAFF can call/recall with assigned queue+resource; CHAIR and DONE require separate explicit per-operator grants; NO_SHOW requires an explicit RECEPTION grant; out-of-order CALL requires queue.override+reason. Resource occupancy, full eligible waiting candidate set, IANA timezone and server time come from the trusted local service. Actor is resolved from the session. Wrong/expired token -> 401; tenant, queue, resource or role mismatch -> 403. Denied commands never append events or update visit state.

Queue snapshot and paged event replay reauthorize on EACH call. Replay cursors are verified to belong to the same tenant and queue. Pagination orders by UTC timestamp, visit ref, aggregate version and event ID for stable equal-timestamp replay. Replay returns minimal event fields and omits purged, unresolvable visit references. This is bounded polling, NOT a long-lived SSE transport.

## FUE-I / reproducible evidence

Test file: queue_core/tests/test_service_auth_08_2_b.py, 11 executable local service scenarios, both SQLite files ephemeral and entirely synthetic. Windows DESKTOP-3MAJEEH / Python 3.12.10. Target suite 11 PASS (11.94s). Final full Queue Core suite after ASCII-only audit-code tightening: 100 PASS (33.65s), exit 0; compileall and git diff --check exit 0. Exact pushed-SHA CI will be verified separately.

Observed workflows:
1. PLANNED visit -> RECEPTION CHECK_IN -> STAFF CALL -> CHAIR -> DONE. Persisted visit versions 0, 2, 3, 5, 7, seven ordered audit events, released chair.
2. Invalid session (401), Admin operational access, RECEPTION call, foreign tenant/queue, non-associated chair and cursor (403), stale version and illegal command: no unauthorized mutation.
3. Rights change revokes old token; a newly logged in operator without queue assignment cannot read/replay/command. Disabled reception loses read rights.
4. NO_SHOW and queue.override enforced by explicit grants and bounded, uppercase audit reason code; events record real actor kind/ref.
5. Stable 2-event-page replay reconstructs all seven equal-timestamp versions in order.
6. Multithreaded revoke attempts while command holds both SQLite locks: no rights change can commit before authorized state/events commit; after rights change old token yields 401.
7. Exceptions roll back real visit state and event log atomically.

## Limitations / Next exact

Not claimed: actual HTTP endpoints, SSE stream reauthorization per emitted event, transport/browser FUE-G, physical Windows acceptance, clinical DB migration, device pairing, release. Physical tests reserved for LOT10. Queue HTTP/SSE product integration belongs to a separately scoped, later step when there is a real transport. PR #1239 remains DRAFT / non-merged; LOT08.2-B remains OPEN. Next: exact-SHA Linux CI + full local Windows tests, update STATE.md and Notion, then determine next authorized transport gate.
