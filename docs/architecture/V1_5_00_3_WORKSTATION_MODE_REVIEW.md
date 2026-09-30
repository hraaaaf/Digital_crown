# V1.5-00.3 — Controlled Workstation-Mode Memory — Security Review

Status: **CLOSEOUT CANDIDATE — not merged, not activated in the cabinet runtime**.

## Goal

Persist an opaque workstation identity server-side and make the workstation mode an authorization boundary, not a frontend preference.

Target experiences:
- `cabinet`: normal authenticated clinical workspace.
- `station`: dedicated reception/kiosk workstation with clinical/admin surfaces locked.
- `control_center`: technical shell; no clinical business data in the current scope.
- Mobile/Pocket and Patient Companion remain separate paired-device trust boundaries.

## Authority model

The browser receives only an opaque `dc_workstation` identity. The authoritative workstation row is stored server-side and scoped to the cabinet tenant. A lost/tampered identity fails closed once the tenant owns workstation state.

Station enforcement is server-backed:
- protected HTTP APIs pass through `get_current_user` and workstation authority;
- the clinical Ghost Insights WebSocket accepts only desktop `access` JWTs;
- long-lived WebSocket sessions revalidate access token/JTI, user, tenant, permission, license and Station authority before each clinical read;
- Bot SSE and accounting streams inherit the central authenticated/permission guard.

## Station escape contract

A temporary Station escape is bound to:
- workstation id;
- tenant id;
- user id;
- current access-session JTI;
- workstation `mode_revision`;
- signed expiration.

Logout revokes the access token and clears the escape cookie. Mode changes and PIN rotation invalidate replay through revision changes. Cross-user, cross-session and cross-tenant reuse are rejected.

## Separate device boundaries

Pocket/Mobile is intentionally not captured by a desktop Station lock. It authenticates with a `mobile` JWT plus live paired-device and tenant checks. A mobile JWT cannot authenticate generic desktop/financial APIs or the clinical desktop WebSocket.

Patient Companion uses its own `patient_companion` device token and tenant/access contract. It is not promoted to a desktop cabinet session.

## Findings closed during adversarial review

1. Clinical WebSocket previously accepted a mobile JWT path — closed: access-token-only.
2. Long-lived WebSocket authorization could outlive later permission/license/tenant changes — closed: revalidation per tick.
3. A WebSocket could survive access-session revocation/logout — closed: token/JTI is redecoded and blacklist-checked per tick.
4. Desktop Station vs Pocket scope was implicit — locked by regression test: desktop remains `423` while a separately paired Pocket device remains authorized.

## Evidence required for final closeout

Local closeout candidate evidence:
- workstation/mobile/patient-companion/migration/release-policy backend suite: 67 tests passing on the current code candidate;
- workstation frontend suite: 19 tests passing;
- Vite test build: 4712 modules + PWA manifest;
- workstation visual harness: 4 states × 3 viewports, zero overflow, expected state visible, zero page/console errors;
- PowerShell desktop shortcut parses and the certified-release shortcut contract test passes;
- Alembic workstation + agenda migration tests pass.

The PR must additionally prove:
- remote branch SHA equals the pushed local closeout SHA;
- CI is green on the PR head;
- exact-head V1.5-00.3 workstation captures/report are recorded and shown for human approval;
- the repository's `UI Human Visual Approval` gate is satisfied by explicit Achraf approval on that exact PR head;
- review has no open P0/P1/P2;
- merge and post-merge checks succeed.

## Non-claims

This review does **not** authorize or assert runtime deployment/activation. The currently installed cabinet runtime remains a separate certified release until an explicit release/activation decision is made.
