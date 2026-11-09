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


## B-2 candidate: durable local operators (2026-11-09)

**Scope:** additive, isolated software/LAB candidate. The G2 B-1 pure policy remains unchanged; B-2 is NOT an HTTP adapter or clinical deployment.

- Implementation: queue_core/security/operator_store.py; synthetic tests: queue_core/tests/test_operator_store_08_2_b.py.
- **One existing local authentication SQLite file from 08.2-A**, not a second inconsistent credential database, and never any clinical DB. The existing restricted Windows filesystem ACL remains the responsibility of the protected A bootstrap/installer path. No automatic installer, route, network port, remote identity provider or default user is added.
- First Admin from A must already be enrolled; one-time binding to a trusted tenant ID requires the A elevated physical-local-console guard and valid live A session. The bootstrapped Admin keeps A credential ownership and recovery semantics. Any untrusted caller's claimed tenant, actor, role or rights are disregarded. A distinct tenant cannot be rebound after first binding.
- Named non-bootstrap operators have per-tenant unique usernames, per-user salted scrypt hashes, lockouts, 8-hour opaque SHA-256-digested sessions, enabled state, role, queue/resource assignments and explicit grants in SQLite.
- Every operator check re-reads session, role, assignments and permissions from the local DB and yields only a trusted VerifiedPrincipal for the existing B-1 QueueAuthorizer. Only Admin may change operators; an Admin role does not imply operational queue rights. New users have no implicit explicit grants. Queue/resource ownership resolution remains a server responsibility: B-2 stores assigned identifiers but cannot certify nonexistent 08.3 server lookups.
- Grant/assignment/role changes and disabling/password reset invalidate affected operator sessions *inside the same BEGIN IMMEDIATE transaction* as the change and append-only audit insert. An audit-write failure rolls the transaction back; protected audit DELETE/UPDATE triggers refuse modification.
- First Admin is immutable within the B-2 operator API and SQL triggers. A last-active-Admin invariant is also checked during rights/disable transactions and enforced by SQL trigger. These are software controls, not evidence of physical operator use.
- A privileged offline recovery in local_auth.recover_admin now atomically clears both 08.2-A and B-2 session tables while preserving existing A behavior when the B-2 table does not exist.
- Invalid login/session, tenant mismatch, disabled account, corrupted role/permission, duplicate username or resolver error fail closed. Never store or log raw sessions, passwords or recovery secrets in audit records.

### Limitations / unproven gates

- **NOT a complete B closeout:** no live API, server target-scope resolver, queue command adapter, SSE authorization/replay, QR lifecycle, native installer or migration of existing production users. No physical first-Admin or multi-operator reception acceptance: LOT10 PHYSICAL NOT_RUN.
- Each QueueAuthorizer check re-resolves from live DB. **Transactionally coupling authorization to future Queue Core command execution** is a mandatory future 08.3 integration condition; the pure resolver alone cannot eliminate in-flight time-of-check/time-of-use races.
- Only one local tenant can be bound to the A first-admin store by this candidate; additional per-machine multi-tenant provisioning is not authorized. Identifiers assigned to queues/resources must later be verified against authoritative Queue Core rows on the server.
- No real patients, clinical DB migration, HTTP user store or production accounts were used. Tests are synthetic and do not establish regulatory/clinical fitness.
- CI and security review at the exact final HEAD, scope review and an independent owner merge decision remain gates; no merge or deployment authorization is implied by implementing B-2.
