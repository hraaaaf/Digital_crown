# DIGITAL CROWN V1.5 — LOT08.2-B RBAC and tenant isolation

**Status: B-1 policy candidate only (DRAFT / not integrated into runtime).**
**Base:** master 324afd13487acf7ff29223f077451927b54b8178, 08.2-A merged.
**Authority:** G2 validated 2026-11-08 in Notion, as corrected by owner 2026-11-09: physical testing belongs exclusively to LOT10.

## Goal / scope

Produce a fail-closed, local-first human permission policy per tenant, queue,
resource, existing visit and action. One role does not silently grant rights
from another role. This first step implements only a pure reusable policy and
adversarial unit oracles. It makes no real operator accounts, persistent
assignments, HTTP routes, SSE, QR issuance or device credentials.

## Validated G2 policy

- ADMIN: manage operators, queues, resources, device pairings and read/export
  tenant-bound audit. No implicit clinical/operational queue action.
- RECEPTION: assigned-queue view, create/admit visits, check-in and issue/revoke
  QR for existing visits. No implicit call, chair, done or global audit.
- STAFF: assigned-queue/resource view, call and recall. CHAIR and DONE require
  separate explicit per-person grants; one never implies the other.
- NO_SHOW: OFF by default for all; explicit grant to RECEPTION only.
- queue.override: OFF by default for everyone; explicit per-person grant,
  valid assigned queue/visit, required nonempty audit reason.
- Kiosk / Wall are *device identities*, not human roles: their pairing, scopes
  and revocation are the separately authorized 08.2-C sublot.
- Resource and visit tenant/queue ownership MUST be resolved server-side from
  storage. Never trust client-supplied scopes, actor/tenant, roles, assignments
  or a claimed authorized flag. Every request and stream subscription/replay
  must be reauthorized against current live session, role, assignments and
  revocation state. No long-lived positive authorization cache.
- Unauthorized or invalid session -> AUTH_REQUIRED (transport mapping 401);
  authenticated but disallowed action/object -> AUTHZ_DENIED (403); no object
  enumeration or cross-tenant disclosure. Caller must check before reading
  the object or invoking Queue Core domain, and before emitting stream events.
- Administrative grant/revoke changes and operational overrides require an
  append-only audit action at the server transaction boundary. A standalone
  policy object is not an audit transaction or authorization service.
- Deleting or disabling last active Admin without an eligible successor is
  forbidden; enforced with durable identity/transaction implementation later
  in this B sublot, not claimed by this B-1 policy.

## Evidence boundary / remaining implementation

B-1 synthetic unit oracles cover role defaults, explicit NO_SHOW, queue.override,
CHAIR/DONE separateness, 401/403, IDOR tenant/queue/visit/resource mismatch,
unassigned resource, immediate revocation/reassignment through a live resolver,
resolver failure, and no Admin implicit operations. Tests use invented IDs,
no passwords, accounts, medical records, or patient data.

B remains OPEN after B-1 until a dedicated local SQLite multi-operator store is
integrated with secure first Admin identity from 08.2-A: per-user password/session,
tenant-bound named account, scoped assignment/grant persistence, atomic
grant/revoke+session invalidation, last-admin guard, audit, safe migration from
A, and an authoritative server-side resolver (no client principal objects).
Tests must exercise concurrent revocation, persistence, tenant isolation and
actual authorization at every queued command and stream adapter introduced
later. No HTTP route or live stream currently exists in 08.2-A/B-1.

Runtime Windows first Admin and physical authorization acceptance are LOT10
(10.1, 10.2, 10.7, 10.8), PHYSICAL NOT_RUN. Code review/CI are LOT08.
No merge/production install/clinical activation without separate GO.
