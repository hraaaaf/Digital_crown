# V1.5-00.4 — Hub & Dispatcher final integration / closeout — START HANDOVER

Date: 2026-09-30
Repository: `hraaaaf/Digital_crown`
Preparation base: `master@962505a201726ff045f21833eb8bfba7af68bc93` (merge PR #722 / V1.5-00.3)
Preparation branch: `docs/v1.5-00-4-start`
Status: PREPARED ONLY — implementation must not start until V1.5-00.3 post-merge closeout is green.

## Why 00.4 exists

The canonical V1.5 roadmap defines **V1.5-00 — Hub & mode dispatcher** as one lot, but does not assign a separate feature contract to a numbered `00.4` sub-lot.
Therefore 00.4 must **not invent a new product feature**.
It is the bounded final integration / residual-gap / closeout pass for V1.5-00 after:
- 00.1: read-only architecture and trust-boundary audit;
- 00.2: real Hub shell + routing;
- 00.3: trusted workstation identity, server-backed mode memory, owner-PIN protected mutation/escape, auditability.

## Goal / Success / Proof

**Goal**: prove that the complete V1.5-00 Hub & Dispatcher contract is coherent on merged master, close only genuine residual gaps, and produce the evidence required to unlock V1.5-01.

**Success**:
- first-launch Hub and remembered workstation dispatch behave as designed;
- Cabinet / Station / Control Center entries preserve their security boundaries;
- Mobile team and Patient Companion remain outside the PC Hub;
- Hub remains business-data-free and fail-soft when backend identity/health is unavailable;
- cabinet identity is canonical and presentation remains premium-clinical;
- touch/responsive behavior is usable at 390x844 / 768x1024 / 1280x900;
- no new parallel state, auth primitive, business logic or V1.5-01 topology work is introduced.

**Proof**:
- exact merged-master audit against 00.1/00.2/00.3 contracts;
- targeted backend/frontend regression and security-negative tests;
- deterministic browser journeys for first launch, remembered modes, Station lock/escape, Control Center and backend-unavailable state;
- BEFORE/AFTER only if a real visual delta is required;
- same three canonical viewports, zero horizontal overflow, console/page errors checked;
- exact-head CI + PostgreSQL where backend/schema changes exist;
- double-check + triple-check with severe scores;
- Human Visual Approval for any changed UI, then merge + post-merge closeout.

## Canonical product decisions to preserve

- First launch -> Hub; later launches -> remembered workstation experience.
- PC Hub exposes only `Digital Crown Cabinet`, `Station d'accueil`, `Centre de controle`.
- Mobile team and Patient Companion retain dedicated entry points.
- Reception PC default is Cabinet; dedicated kiosk boots Station.
- Cabinet can expose `Changer d'espace` only in authorized context.
- Station has no patient-visible Hub exit; escape requires protected admin flow + owner PIN.
- Workstation mode belongs to the workstation, not the logged-in user.
- Permanent mode change is server-authorized and audited; local storage is never authority.
- Hub is neutral/common and contains no patient/agenda/accounting/business payload.
- Backend unavailable: Hub stays available and Control Center/diagnostic path remains reachable without exposing clinical data.
- Station remains tablet/touch compatible.
- Visible identity reuses canonical clinic identity (`nom_cabinet`, `cabinet_type`, existing logo path where applicable); no parallel cabinet identity store.

## Start audit — exact merged master

Verified preparation base is the actual PR #722 merge commit `962505a2...`.
Current Hub implementation files are concentrated under `frontend/src/features/hub/`, with routing in `frontend/src/App.tsx` and server authority in `backend/routers/workstation_mode.py`.
No repository document found a pre-existing canonical feature definition for `V1.5-00.4`; this handover intentionally treats 00.4 as closeout, not scope expansion.

## Mandatory execution order

1. Confirm V1.5-00.3 post-merge full backend gate is SUCCESS; otherwise stop and repair 00.3 first.
2. Rebase/refresh 00.4 implementation branch from the resulting certified `master`.
3. Read in order:
   - `docs/architecture/V1_5_00_1_HUB_DISPATCHER_READONLY_AUDIT.md`
   - `docs/architecture/V1_5_00_2_HUB_SHELL_CLOSEOUT.md`
   - `docs/architecture/V1_5_00_3_WORKSTATION_MODE_REVIEW.md`
   - this handover.
4. Build a requirement matrix: every retained V1.5-00 product decision -> code path -> test -> observed proof.
5. Audit before coding. Classify every finding as `already satisfied`, `real residual gap`, or `belongs to V1.5-01+`.
6. Implement only real residual V1.5-00 gaps. No speculative polish and no topology/LAN/warm-standby work.
7. If UI changes: capture BEFORE first, define target/mockup, then AFTER at identical viewports.
8. Run targeted tests locally on the remote workstation, then build/runtime/browser proof.
9. Commit, push branch, verify remote SHA, open PR, exact-head CI/reviews.
10. Human gate if UI changed; merge only after all required gates are green; post-merge; update canonicals; clean worktree.

## Explicit exclusions

- V1.5-01 topology, LAN discovery/configuration, server/backup-PC failover, network diagnostics/install docs beyond what the existing Control Center shell already truthfully exposes.
- V1.5-02 patient identity/photo.
- V1.5-03 kiosk patient workflow, waiting-room business state, QR/NFC.
- V1.5-04 self-service documents/signature.
- V1.5-05 remote arrival queue.
- V1.5-06 SQL migration, V1.5-07 imaging gateway, V1.5-08 theme packs/motion.
- No Vercel deployment.
- No production/cabinet runtime activation.

## Known audit traps

- `/salle-attente` is still a separate ComingSoon route; do not pull waiting-room implementation into 00.4.
- `appMode` remains legacy demo/prod state; never repurpose it as workstation authority.
- Hub presentation can reuse theme tokens, but Theme Packs belong to V1.5-08.
- Control Center in V1.5-00 is an entry/shell and fail-soft destination, not the V1.5-01 network-topology product.
- A clean closeout with **zero product-code delta** is acceptable if the matrix proves the V1.5-00 contract already complete.

## Closeout gates

Do not call V1.5-00 closed until all applicable evidence is observable.

Minimum closeout:
- 00.3 certified post-merge base;
- V1.5-00 requirement matrix complete with no unexplained gap;
- local targeted regression green;
- browser journeys green for Hub/Cabinet/Station/Control Center and fail-soft state;
- security-negative cases preserve fail-closed Station/workstation authority;
- exact-head CI green;
- PostgreSQL certification green if schema/backend persistence changes;
- visual proof + Achraf approval if UI changes;
- double-check and triple-check recorded;
- merge and post-merge evidence green;
- canonical roadmap/handover updated;
- V1.5-01 unlocked only after that closeout.

### Reviewer prompt — double check

`Review V1.5-00.4 independently on the exact candidate HEAD. Try to disprove that the complete Hub & Dispatcher contract is closed. Inspect routing precedence, workstation authority, Station escape, direct-URL/storage tampering, Mobile/Patient Companion isolation, backend-unavailable behavior, business-data leakage, responsive/touch behavior and evidence integrity. Report P0/P1/P2 findings, missing proof and a severe score /10. Do not approve from documentation claims alone.`

### Reviewer prompt — triple check

`Perform a second adversarial review of V1.5-00.4 from a different angle: regression, operator recovery, stale/missing workstation identity, cross-user/cross-tenant/session replay, long-lived channel implications, accessibility/touch, offline/fail-soft truthfulness, and scope leakage into V1.5-01+. Re-run or inspect independent evidence on the exact HEAD. Report blockers and a severe score /10; explicitly challenge the first review.`
