# Auth Context

This file is the canonical Auth context entrypoint for DigitalCrown.

Use it after `process/context/all-context.md` when the task needs authentication flows, JWT token management, or route guards.

---

## Scope

This group covers:

- Local JWT token generation, expiration, validation, and refresh token rotation logic in `backend/security.py` and `backend/routers/auth.py`.
- Supabase Auth sync/bridging (mapping Cloud auth events to Local tokens).
- Route guards and role permission checks (e.g., `require_permission`, `require_elite_license`).
- Mobile Auth QR Code tokens and claims.

It does not cover:

- Network port proxying or firewall configuration (that belongs in system architecture).
- UI login layout designs (that belongs in `uxui/` context).

## Read When

Read this entrypoint when:

- modifying JWT secret validation, lifetimes, or payload structures
- correcting API endpoint protection rules or adding role requirements
- troubleshooting Supabase session synchronization issues
- implementing mobile authentication steps

## Quick Routing

- use `backend/security.py` for JWT signing and password hashing
- use `backend/routers/auth.py` for authentication routing endpoints
- use `frontend/src/services/auth.ts` for frontend token storage and user session synchronization

## Source Paths

- `process/context/auth/all-auth.md`

## Update Triggers

Update this group when:

- auth schemas or token generation logic in backend is updated
- Supabase integration setup or client libraries are updated
- role permissions or licensing check guards are modified
