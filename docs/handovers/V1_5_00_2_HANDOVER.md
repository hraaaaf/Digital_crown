# HANDOVER ? Digital Crown V1.5-00.2 ? V1.5-00.3

Date: 2026-09-30
Repository: hraaaaf/Digital_crown
Remote workstation: DESKTOP-3MAJEEH

## Canonical starting point

V1 is operational and closed.
V1.5-00.2 is closed and merged.

- pre-00.2 architecture audit: `db1cadd74eb60d3e11e6c31d5da6780fefaacbb4`;
- approved PR head: `d257202d6a882c23fac8597084cdb0a1b4087f46`;
- PR: #719 ? MERGED;
- merge commit: `9b135e5dbad3b13b289cf2de78784959060f52b3`;
- human visual gate: SUCCESS after explicit Achraf approval;
- closeout: `docs/architecture/V1_5_00_2_HUB_SHELL_CLOSEOUT.md`.

Before starting 00.3, fetch `origin/master` and use the actual current master SHA. Do not assume the merge SHA above is still repository HEAD if master has advanced.

## What 00.2 implemented

- authenticated desktop root -> `/hub`;
- data-free `/hub` dispatcher;
- protected `/cabinet` entry to existing Cabinet surface;
- `/station` shell only;
- `/control-center` shell only;
- Cabinet header -> `Changer d'espace`;
- Mobile team and Patient Companion remain separate;
- main product card = `Digital Crown` with dynamic `CABINET` / `CLINIQUE` badge;
- Hub remains available when clinic identity lookup fails;
- Hub visual primitives inherit canonical theme tokens;
- no workstation-mode state is stored in legacy `appMode`.

## Verified evidence

Merged-master independent review:

- Hub targeted tests: 2 files / 7 tests PASS;
- local `npm run build:test`: PASS;
- 4745 modules transformed;
- PWA generated;
- no forbidden visual hardcodes in Hub surfaces;
- tampered `localStorage.appMode` did not bypass `/cabinet` authentication;
- Prestige persisted theme inherited correctly;
- mobile direct Hub at 390px had no horizontal overflow.

Human visual approval was explicitly given by Achraf for the Clinic rendering before PR #719 merged.

## Security boundary ? carry forward unchanged

00.2 does not provide:

- secure Station lock;
- permanent workstation-mode persistence;
- owner/admin PIN enforcement;
- trusted workstation identity;
- server-authorized mode mutation.

Station and Control Center are deliberately non-business shells. Do not promote them to operational workstation modes until 00.3 closes its security contract.

## V1.5-00.3 ? next exact scope

Goal: controlled workstation-mode memory and secure permanent mode changes.

Required contract:

- workstation mode is separate from legacy `appMode`;
- workstation identity belongs to the device, independent of logged-in user;
- first launch goes to Hub when workstation mode is not configured;
- configured workstation remembers its default experience;
- classic reception PC may default to Cabinet;
- dedicated kiosk may default to Station;
- permanent mode change requires authorized admin/owner + server-verified owner PIN;
- Station exit to Hub requires protected admin action + PIN;
- local storage may cache convenience state but cannot authorize anything;
- direct URL/storage tampering must not bypass RBAC or Station lock;
- changes must be auditable;
- workstation identity must take precedence over the current viewport-only mobile redirect for dedicated tablet/kiosk devices.

## Known repo debt not introduced by 00.2

A post-merge production dependency audit observed existing vulnerabilities, including axios/react-router related findings. No package dependency delta was introduced by 00.2. Treat this as separate repository debt; do not silently fold dependency upgrades into 00.3 unless explicitly scoped and tested.

## Execution rule

Work directly on DESKTOP-3MAJEEH through Remote Desktop Commander. GitHub Actions are secondary CI evidence, not the primary implementation environment.

## Required first actions in the next conversation

1. Read this handover.
2. `git fetch origin master`.
3. Verify current `origin/master`, worktree cleanliness, PR/CI state.
4. Read the 00.2 closeout and the 00.1 read-only architecture audit.
5. Do not reimplement the Hub.
6. Start 00.3 with an explicit workstation-mode threat model before persistence or PIN implementation.
