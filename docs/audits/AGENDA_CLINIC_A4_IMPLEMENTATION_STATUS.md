# Agenda Clinique A4 — implementation checkpoint

Date: 2026-09-17

## Goal
Model physical clinic capacity with optional tenant-scoped resources and prevent overlapping exact-time use of the same capacity-1 resource without weakening A1-A3.

## Implemented on branch
- `agenda_resources` additive persistence model and Alembic migration.
- nullable `appointments.resource_id`, no historical backfill, FK `ON DELETE SET NULL`.
- resource CRUD contract (`CHAIR`, `ROOM`, `OTHER`) with tenant isolation and activation state.
- appointment schemas expose optional `resource_id`.
- deterministic resource collision service: NULL does not block; tenant isolation; inactive/new assignment fail-closed; exact-time overlap; current-row exclusion.
- focused service and static contract tests added.

## Not yet claimed complete
- The A4 child router installer exists but still requires one surgical mount into the existing `/agenda` router startup path.
- Resource collision service still requires wiring into appointment create, update, bulk and check-conflicts.
- Full backend/PostgreSQL/CI proof is pending.
- UI BEFORE/mockup/AFTER has not started; no visual code has been changed.
- A4 closeout and merge are not authorized until exact-head proof and explicit user merge approval.

## Safety invariants
- `resource_id = NULL` is valid and never a global blocker.
- Practitioner legacy NULL semantics remain unchanged.
- No resource backfill or silent assignment.
- Cross-tenant resources are never assignable.
- Inactive resources remain historical/readable but cannot be newly assigned.
- A resource collision is independent from a practitioner collision.
