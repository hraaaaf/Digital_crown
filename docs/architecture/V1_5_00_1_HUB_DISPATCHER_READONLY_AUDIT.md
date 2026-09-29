# V1.5-00.1 - Hub & Dispatcher read-only audit

Date: 2026-09-29
Repository: hraaaaf/Digital_crown
Base master: `7401f40254ef9e33f21f036a8e897e2998b87915`
Branch: `feat/v1.5-00-hub-dispatcher`

## Goal / Success / Proof

Goal: define the Hub/Dispatcher architecture before any product mutation.

Success:
- preserve existing Cabinet, Mobile team and Patient Companion flows;
- define the three PC Hub experiences: Digital Crown Cabinet, Station d'accueil, Centre de controle;
- define first-launch and workstation-mode rules without weakening RBAC;
- identify the exact integration points and blockers for V1.5-00.2;
- no product/runtime code change in this sub-lot.

Proof:
- direct audit of current master routing, auth, RBAC, cabinet identity and storage;
- contradiction/gap inventory below;
- docs-only diff and clean git status after commit.

## Canonical product decisions retained

- First launch: Hub first, then remember the workstation default experience.
- PC Hub exposes only: Digital Crown Cabinet / Station d'accueil / Centre de controle.
- Mobile team and Patient Companion keep their dedicated entry points.
- Reception PC defaults to Digital Crown Cabinet.
- Dedicated kiosk starts directly in Station d'accueil.
- Cabinet -> Hub: user menu action "Changer d'espace".
- Station -> Hub: no patient-visible exit; admin action + owner PIN only.
- Workstation mode belongs to the workstation, not to the logged-in user.
- Permanent workstation-mode change: admin-only + owner PIN.
- Hub stays neutral/common and is a dispatcher only: no business data.
- If the server is unavailable, Hub remains available with diagnostics / Centre de controle.
- Station must remain tablet/touch compatible.
## Current master - verified architecture

### Root routing

`frontend/src/App.tsx` owns the desktop/mobile root dispatch.

Current `SmartRootRouter` behavior:
- mobile -> `/mobile/dashboard`;
- authenticated desktop -> `/dashboard`;
- anonymous desktop -> `/landing`.

This is the natural integration point for the V1.5 workstation dispatcher.

### Existing Cabinet surface

The current protected desktop application already provides the Cabinet experience.
The V1.5 architecture must reuse it rather than duplicate its routes, layouts or data flows.

Recommended stable entry:
- `/cabinet` -> existing protected Cabinet surface / dashboard contract.

The existing `/dashboard` and all current business routes remain internal Cabinet routes.

### Existing dedicated surfaces

- Mobile team already has dedicated `/mobile/*` routes and `MobileProtectedRoute`.
- Patient Companion already has the separate `/companion` boundary.
- Neither should be routed through the PC Hub.

### Existing waiting-room route

`/salle-attente` currently renders a ComingSoon surface.
It is not a Station d'accueil implementation and must not be treated as one.
## Security and authority findings

### RBAC

`frontend/src/utils/accessControl.ts` is the canonical frontend permission helper.

Verified behavior:
- superadmin -> all frontend permissions;
- ADMIN -> all frontend permissions;
- owner dentist = DENTISTE with `employer_id === null` -> all frontend permissions;
- employee/secretary behavior follows explicit permissions or legacy defaults;
- unknown/partial identities fail closed.

Important: the file itself states frontend RBAC never replaces backend controls.

### Authentication

`useAuthStore` persists user/auth state and refreshes the full profile from backend auth services.

V1.5 workstation mode must not become an authentication or authorization primitive.

### Existing appMode

`safeStorage['appMode']` is currently used for legacy demo/prod behavior.
It is initialized by `ProtectedRoute`, cleared on logout, and referenced by Settings.

Decision: DO NOT reuse `appMode` for the V1.5 workstation experience.

A separate, explicit workstation-mode contract is required.

### Owner PIN / admin PIN

Repository search found no current owner-PIN or admin-PIN verification mechanism.

Therefore:
- no PIN may be stored or trusted as plaintext/localStorage data;
- local browser storage cannot authorize Station escape or permanent mode changes;
- V1.5 implementation needs a server-verified owner-PIN contract before protected mode changes are considered complete.
## Cabinet identity reuse

Current cabinet identity is already available through `GET /clinics/me`.

Verified reusable fields include:
- `nom_cabinet`;
- `cabinet_type`;
- `logo_path`.

The Hub must consume the canonical cabinet identity instead of introducing a parallel identity store.

Visible identity per product decision:
- Digital Crown;
- cabinet commercial name;
- configured establishment type.

No business dashboard data belongs on the Hub.

## Required V1.5 dispatcher model

Proposed enum:
- `cabinet`
- `station`
- `control_center`

These values describe workstation experience only.
They do not grant permissions.

Proposed stable entries:
- `/hub`
- `/cabinet`
- `/station`
- `/control-center`

Routing rule:
1. Mobile UA/viewport continues to existing mobile route behavior.
2. Patient Companion remains explicit `/companion`.
3. Desktop workstation with no configured mode -> Hub.
4. Configured workstation -> remembered default experience.
5. Authorized user may return to Hub according to experience-specific rules.
## Trust model

Convenience persistence and security authority must be separated.

Allowed local responsibility:
- remember the workstation's preferred/default experience;
- allow boot-time routing even before all business data loads.

Not allowed local authority:
- grant admin rights;
- validate owner PIN;
- unlock Station escape;
- authorize permanent workstation-mode mutation.

Permanent mode changes require:
- authenticated authorized user;
- backend-enforced admin/owner authorization;
- server-verified owner PIN;
- auditable change event.

Station direct URL navigation or localStorage manipulation must not bypass this contract.

## Server unavailable behavior

Current `ProtectedRoute` waits for backend `/health` before rendering the protected application.

That behavior conflicts with the Hub requirement that the Hub remain available when the server is down.

Implementation consequence:
- `/hub` must sit outside the backend-dependent Cabinet `ProtectedRoute`, or use a separate fail-soft shell;
- Cabinet business routes remain backend/auth dependent;
- Hub may show diagnostic state and allow entry to Centre de controle without exposing clinical data.
## V1.5-00.2 implementation boundary

Only after this read-only contract is accepted/merged:

1. Introduce a dedicated workstation-mode model/service; never overload `appMode`.
2. Add Hub-level routing above Cabinet `ProtectedRoute`.
3. Add stable entries `/hub`, `/cabinet`, `/station`, `/control-center`.
4. Preserve existing `/dashboard` Cabinet internals.
5. Reuse `useAuthStore`, `hasAccess`, and `/clinics/me`.
6. Add the protected owner-PIN backend contract before permanent mode changes / Station escape.
7. Add "Changer d'espace" in the Cabinet user menu only for authorized contexts.
8. Keep Hub free of patient/agenda/accounting/business payloads.
9. Implement first-launch -> Hub and subsequent workstation default routing.
10. Add tests for direct URL attacks, storage tampering, backend unavailable behavior and mobile/Companion non-regression.

## UI/UX proof rule for 00.2

00.1 is read-only and has no product UI delta.
No screenshots are fabricated for this sub-lot.

00.2 must follow:
BEFORE -> written Goal -> reference/mockup -> implementation -> AFTER at the same viewports -> comparison -> tests -> severe visual score.

Canonical viewports:
- 390x844
- 768x1024
- 1280x900

## Read-only conclusion

The existing codebase is structurally reusable for V1.5-00.

No current trusted workstation-mode contract exists.
No owner/admin PIN verification contract exists.
Those two gaps are the mandatory security foundation for the Dispatcher.

00.1 does not authorize UI implementation by itself; it defines the exact contract that 00.2 must satisfy.
