# NEXT — Staff clinic identity & Clinical Library permissions (independent)
Status: PREPARED / NOT EXECUTED. Base: master @ c3b094d8e5e8ba52ca40e7521927c0c5d60326a9.
Working branch: audit/staff-clinic-library-rbac. No merge or deploy authorized.

## Goal & observable success
Certify, using disposable accounts and real browser+backend, that secondary staff stations resolve **their actual cabinet identity**, and that access to the Clinical Library is **intentional and enforced**. No broad runtime modification without a verified defect. Tests must prove exact HEAD and be accompanied by before/after screenshots on the **same screen** at 390x844 and 1280x900.

## Verified baseline (distinct from product certification)
- PR #803 CLOUD-LAB S+A+B+C+D, run https://github.com/hraaaaf/Digital_crown/actions/runs/37865730938 : 13/13 TLS/API phases, 4/4 Chromium contexts, 8 snapshots, cloud-only. Hub Dispatcher run https://github.com/hraaaaf/Digital_crown/actions/runs/37865731031 : 12/12 journeys, 149/149 assertions. BOTH green on PR #803's exact HEAD df2b408b17d47c0e81318fe6d0248e000a9a5940. Do not merge these experimental validations into this branch.
- Prior PR #803 screenshot inspection showed A/B header "Cabinet T2 Certification" but C/D "Centre Dentaire Benmoussa", empty active-cabinet selector. **This does not prove a cross-tenant leak**.
- On **master**, `frontend/src/components/Header.tsx` has **already removed the hardcoded "Centre Dentaire Benmoussa" fallback**. It fetches actual staff cabinet via `/admin/cabinet/me` (for non-settings users) or `cabinetApi.getMine()` (settings users) and has guarded state updates on user change. FIRST run verification; do not duplicate or regress existing fix.
- On **master**, `frontend/src/components/Sidebar.tsx` displays `/bibliotheque` unconditionally; `frontend/src/App.tsx` routes `/bibliotheque` and `/bibliotheque/:code` without a specific `PermissionRoute`. This is a **policy question**, not yet an established privilege vulnerability. The library may contain general reference material intentionally accessible to staff.
- T2 Runtime workflow https://github.com/hraaaaf/Digital_crown/actions/runs/37865731091 stays FAILED on absent `frontend/scripts/audit-first-user-experience{,-b}.mjs`. Do not claim this independent work replaces those missing oracles.

## Execution sequence
1. Record current master HEAD, exact baseline routes, existing owner/restricted-user test fixtures and relevant CI gates. Before changing code, verify `GET /api/admin/cabinet/me` or `/admin/cabinet/me` response status, tenant scoping and authorization for restricted staff, plus header and active-cabinet selector after sign-in/reload/stale localStorage/user-switch.
2. Inspect `EliteLibrary`, `EliteScienceHub`, `Sidebar`, `App` and their backend data/API contracts. Document whether reference library content is truly clinical/patient-sensitive or general-purpose reference. Decide allowed roles **from product policy/source**, not assumption. Capture direct URL access for C/D and API responses; reject unauthorized access server-side if policy requires.
3. Build small, exact-HEAD, synthetic multi-session browser tests covering owner A/B and staff C/D, patients denial, no cross-tenant data, controls and deep links, site identity after recovery and viewport 390x844/1280x900. Failed authentication/no backend must fail closed. Preserve TLS and session isolation.
4. If a verified defect exists, make the smallest product change and tests on this independent branch only. No change if already correct; document the evidence.
5. Capture same-screen BEFORE and AFTER, inspect all actual images; report P0/P1/P2 with severity. Run focused frontend/backend tests and the relevant required CI. Use two independent **internal** adversarial perspectives on identical final HEAD, then reverify after any changes.
6. POST evidence/run URLs, exact SHA, test outcomes, Notion link and blockers. No merge/deploy without user approval. No Windows physical/LAN certification inferred from Docker proof.

## PASS criteria
- A/B/C/D display the correct tenant header/cabinet identity; no hardcoded fallback to another brand and no cross-tenant data; staff permitted endpoints explicit.
- C/D sidebar and direct library routes consistently follow a **documented** least-privilege policy, checked in backend and frontend where appropriate.
- All added true behavior tests pass on exact HEAD; snapshots at matching viewports inspected, no material P0/P1 unresolved. Required/experimental/out-of-scope CI gates classified. Otherwise mark OPEN/BLOCKED, do not invent PASS.

Canonical reference: https://app.notion.com/p/3f377c6633628187a51ee94a983d7267
