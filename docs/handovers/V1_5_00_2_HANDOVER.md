# HANDOVER — Digital Crown V1.5-00.2 → V1.5-00.3

Date: 2026-09-30

Repository: hraaaaf/Digital_crown
Remote workstation: DESKTOP-3MAJEEH
Worktree: C:\Users\lenovo\Documents\Cabinet\DigitalCrown-v1.5-00
Branch: feat/v1.5-00-2-hub-implementation

## Canonical starting point

V1 is operational and closed.
V1.5-00.1 read-only architecture audit:
- commit: db1cadd74eb60d3e11e6c31d5da6780fefaacbb4
- document: docs/architecture/V1_5_00_1_HUB_DISPATCHER_READONLY_AUDIT.md

V1.5-00.2 implementation chain:
- implementation: 79fea6647283dc9553e89ad102c5d137e4a05883
- closeout: 97474038e8253016cfed86bf371dccb234525ba5
- handover/merge-gate state before final metadata refresh: d439a5cbd35bb929b8bdf91daea5dec577864d51

## What 00.2 implemented

- authenticated desktop root now dispatches to /hub;
- /hub added as data-free workstation dispatcher;
- /cabinet added as protected alias to the existing Cabinet/dashboard surface;
- /station added as a shell only;
- /control-center added as a shell only;
- Cabinet header exposes "Changer d'espace";
- Mobile team and Patient Companion remain separate;
- legacy appMode is not reused as workstation-mode state;
- Hub cabinet identity reads /api/clinics/me using the runtime auth token;
- backend identity failure does not remove the Hub;
- explicit offline Hub state exists.

## Security boundary

00.2 does NOT claim:
- secure Station lock;
- permanent workstation-mode persistence;
- owner/admin PIN enforcement;
- trusted workstation identity;
- server-authorized mode mutation.

Those belong to 00.3.

Station must remain fail-closed until the 00.3 protected mode-change contract exists.
LocalStorage or direct URL navigation must never become authorization authority.

## Local verification already observed

Targeted tests:
- frontend/src/features/hub/HubPage.test.tsx
- frontend/src/test/v15HubRoutingContract.test.ts
- result: 2 files / 5 tests PASS.

Visual proof on DESKTOP-3MAJEEH:
- 390x844: Hub present, 3 cards, no horizontal overflow;
- 768x1024: Hub present, 3 cards, no horizontal overflow;
- 1280x900: Hub present, 3 cards, no horizontal overflow;
- refined online fixture produced zero JS errors;
- offline behavior was separately observed and tested.

Severe visual review:
- mobile 9.0/10
- tablet 9.0/10
- desktop 9.1/10
- internal triple-check 8.9/10

## Evidence files

Closeout:
- docs/architecture/V1_5_00_2_HUB_SHELL_CLOSEOUT.md

BEFORE captures:
- artifacts/v1.5-00.2-local/before/hub-390x844-final.png
- artifacts/v1.5-00.2-local/before/hub-768x1024-final.png
- artifacts/v1.5-00.2-local/before/hub-1280x900-final.png

Final AFTER captures:
- artifacts/v15-00-2-refined/hub-390x844.png
- artifacts/v15-00-2-refined/hub-768x1024.png
- artifacts/v15-00-2-refined/hub-1280x900.png

## Required first actions in the next conversation

1. Read this handover.
2. Verify actual repo state on DESKTOP-3MAJEEH:
   - git fetch origin master
   - current branch
   - HEAD
   - git status
   - PR/merge state if one exists
3. Verify V1.5-00.2 closeout proof. Local exact-HEAD verification on `d439a5cbd35bb929b8bdf91daea5dec577864d51`: 2 files / 5 tests PASS + `npm run build:test` PASS (4709 modules, PWA assets generated).
4. Do not reimplement the Hub.
5. Start V1.5-00.3 only after 00.2 is formally closed.

## V1.5-00.3 — next exact scope

Goal: controlled workstation-mode memory and secure permanent mode changes.

Required contract:
- separate workstation-mode model from legacy appMode;
- mode belongs to workstation, independent of logged-in user;
- first launch goes to Hub;
- configured workstation remembers default experience;
- classic reception PC defaults to Cabinet;
- dedicated kiosk may default to Station;
- permanent mode change requires authorized admin/owner + server-verified owner PIN;
- Station exit to Hub requires protected admin action + PIN;
- local storage may remember convenience state but cannot authorize anything;
- direct URL or storage tampering must not bypass RBAC or Station lock;
- all changes must be auditable.

## Execution rule

Work directly on DESKTOP-3MAJEEH through Remote Desktop Commander.
GitHub Actions are secondary CI evidence only, never the primary implementation or validation environment.

## GitHub closeout status

- PR: #719
- URL: https://github.com/hraaaaf/Digital_crown/pull/719
- PR head before this handover metadata refresh: d439a5cbd35bb929b8bdf91daea5dec577864d51
- mergeable: YES
- current merge state: UNSTABLE
- local implementation/testing/build/visual proof: COMPLETE
- blocking check: Human visual approval (Achraf) = FAILURE because no explicit human approval has been recorded yet
- other GitHub checks are secondary and may still be running/queued; re-check actual state on resume

Do not claim 00.2 fully merged/closed until Achraf explicitly approves the observed AFTER visuals and PR #719 is merged.
