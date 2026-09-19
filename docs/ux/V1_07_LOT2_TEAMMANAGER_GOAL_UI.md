# V1-07 — LOT 2 TeamManager — Goal UI

Date: 2026-09-19

## Goal
Make TeamManager button states truthful, fail-closed and resistant to accidental duplicate mutations without redesigning the existing surface.

## BEFORE risks
- GOLD 1/1 dentist + 0/2 assistants can display a generic full-pack warning even though assistant capacity remains.
- Team load failure can appear as a false empty-team state.
- A rejected identity can expose a Reactivate action.
- Reject/delete/suspend/reactivate/permission-save can accept duplicate user actions while a mutation is in flight.

## Target
- GOLD partial quota names the saturated role and remaining assistant capacity.
- Load failure shows an explicit retryable error and never the empty-team illustration.
- Rejected identity keeps its Refusé badge and exposes no Reactivate/Suspend toggle.
- Mutations are single-flight.
- Backend independently rejects reactivation and stale access/refresh reuse for rejected sub-accounts.

## Evidence
Matched BEFORE/AFTER viewports:
- 1024 × 900
- 1440 × 1000

Scenarios:
1. GOLD partial quota.
2. Team load failure.
3. Rejected identity action row.

No Vercel deployment.
